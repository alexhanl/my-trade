import akshare as ak
import matplotlib.pyplot as plt
import pandas as pd
import datetime as dt
import os

plt.rcParams["font.sans-serif"] = ["SimHei"]  # 设置字体
plt.rcParams["axes.unicode_minus"] = False    # 该语句解决图像中的“-”负号的乱码问题

NET_VALUE_DATE = '净值日期'
ACCU_NET_VALUE = '累计净值'
TOTAL_INVESTMENT = 100.0

DATA_PATH='./data'

def download_and_save_fund_raw_data(ticker: str):
    """ 利用 akshare 下载基金累计净值数据， 并且存放到data/<ticker>.csv文件中 """
    data = ak.fund_open_fund_info_em(fund=ticker, indicator="累计净值走势")
    filename = ticker + '.csv'
    data.to_csv(os.path.join(DATA_PATH, filename), index=False)

def load_potifolio_funds_data(ticker_series: pd.Series, start_date, end_date) -> dict:
    """ 获取portfolio 中每个基金的累计净值数据
    Parameters:
    ticker_series (pd.Series): 参数1的描述
    start_date
    end_date

    Returns:
    dict: dict 映射 ticker -> 净值数据(pd.DataFrame)
    """
    data_dict = {}
    for ticker in ticker_series:
        data_dict[ticker] = fill_non_trade_day_data(load_fund_data(ticker, start_date, end_date), start_date, end_date)  
    return data_dict

def load_fund_data(ticker, start_date, end_date) -> pd.DataFrame:
    ''' 从 csv 文件中读取加载基金累计净值数据，并且只截取 [start_date, end_date] 区间的数据
    
    Returns:
    pd.DataFrame: 一个单列的dataframe, index为时间, column为 '累计净值'
    '''
    data_df = pd.read_csv(os.path.join(DATA_PATH, ticker + '.csv'))
    data_df[NET_VALUE_DATE] = pd.to_datetime(data_df[NET_VALUE_DATE])   
    data_sliced_df = data_df[(data_df[NET_VALUE_DATE] >= start_date) & (data_df[NET_VALUE_DATE] <= end_date)]
    data_sliced_df.set_index(NET_VALUE_DATE, inplace=True)
    return data_sliced_df



def fill_non_trade_day_data(data_df, start_date, end_date) -> pd.DataFrame:
    ''' 填补非交易日的数据 '''
    
    # 如果 start_date 是非交易日
    if data_df[ACCU_NET_VALUE].get(start_date) == None:
        first_trade_day_net_value = data_df[ACCU_NET_VALUE].iloc[0]
        start_date_df = pd.DataFrame({NET_VALUE_DATE: [start_date], ACCU_NET_VALUE: [first_trade_day_net_value]})
        start_date_df.set_index(NET_VALUE_DATE, inplace=True)
        data_df = pd.concat([start_date_df, data_df])
    
    # 填补后面的非交易日
    for i in range((end_date-start_date).days):
        date = start_date + pd.DateOffset(i+1)        
        net_value = data_df[ACCU_NET_VALUE].get(date)
        if net_value == None:  # 非交易日，用上一个交易日的数据替代
            last_day_net_value = data_df[ACCU_NET_VALUE].get(date - pd.DateOffset(1))
            date_df = pd.DataFrame({NET_VALUE_DATE: [date], ACCU_NET_VALUE: [last_day_net_value]})
            date_df.set_index(NET_VALUE_DATE, inplace=True)
            data_df = pd.concat([data_df, date_df])
    
    data_df = data_df.sort_index()  
    return data_df

def calculate_max_dd(value_series: pd.Series):  
    ''' 计算最大回撤 '''
    start_date = value_series.index[0]
    end_date = value_series.index[-1]
    
    dd_peak_date_candidate = dd_peak_date = value_series.index[0]
    dd_bottom_date_candidate = dd_bottom_date = dd_peak_date
    dd_peak_value_candidate = dd_peak_value = value_series.iloc[0]
    dd_bottom_value_candidate = dd_bottom_value = dd_peak_value
    max_dd_candidate = max_dd = dd_peak_value - dd_bottom_value
    
    for i in range((end_date-start_date).days):
        today = start_date + pd.DateOffset(i+1)
        today_value = value_series[today]
        
        if (today_value > dd_peak_value):  # 一个下跌周期计算结束
            
            max_dd = dd_peak_value - dd_bottom_value
            if (max_dd > max_dd_candidate): # 当前的回撤更高
                dd_peak_date_candidate = dd_peak_date
                dd_bottom_date_candidate = dd_bottom_date
                dd_peak_value_candidate = dd_peak_value
                dd_bottom_value_candidate = dd_bottom_value
                max_dd_candidate = max_dd
                
            # 新的可能的下跌周期开始
            dd_peak_date = dd_bottom_date = today
            dd_peak_value = dd_bottom_value = today_value
                    
        elif (today_value < dd_bottom_value):  # 继续下跌
            dd_bottom_date = today
            dd_bottom_value = today_value
    
    # 计算最后一个周期
    max_dd = dd_peak_value - dd_bottom_value      
    if (max_dd > max_dd_candidate): # 当前的回撤更高 查看最后一个
        dd_peak_date_candidate = dd_peak_date
        dd_bottom_date_candidate = dd_bottom_date
        dd_peak_value_candidate = dd_peak_value
        dd_bottom_value_candidate = dd_bottom_value
        max_dd_candidate = max_dd   
    
    return max_dd_candidate, dd_peak_date_candidate, dd_bottom_date_candidate, dd_peak_value_candidate, dd_bottom_value_candidate  
        

def back_trade(portfolio_df, start_date, end_date, rebalance_period, funds_data_dict):
    fund_value_dict = {}  # map of fund ticker to fund_value_df
    # portfolio_value_list = None
    portfolio_value_series = pd.Series()

    # calculate the initial number of shares, fund value and total fund value
    for index, row in portfolio_df.iterrows():
        ticker = row['ticker']
        target_percent = row['target_percent']

        start_date_net_value = funds_data_dict[ticker][ACCU_NET_VALUE].iloc[0]
        fund_value = TOTAL_INVESTMENT * row['target_percent'] / 100 
        shares = fund_value / start_date_net_value
        
        fund_value_dict[ticker] = pd.DataFrame([[start_date, start_date_net_value, shares, fund_value]], 
                                               columns=['date', 'net_value', 'shares', 'fund_value'])

    # 计算start date的初始 portfolio 整体 value，在没有佣金的情况下，应该为 TOTAL_INVESTMENT，也就是100
    portfolio_value = 0.0 
    for ticker in portfolio_df['ticker']:
        portfolio_value = portfolio_value + fund_value_dict[ticker]['fund_value'].iloc[0]

    # portfolio_value_list = [portfolio_value]
    portfolio_value_series[start_date] = portfolio_value


    # 计算每天的基金价值变化，从第二天开始
    for i in range((end_date-start_date).days):
        date = start_date + pd.DateOffset(i+1)        
        
        portfolio_value = 0.0
        for ticker in portfolio_df['ticker']:
            net_value = funds_data_dict[ticker][ACCU_NET_VALUE].get(date)
            shares = fund_value_dict[ticker]['shares'].iloc[-1]  # 在没有交易的情况下，份额保持不变
            fund_value = net_value * shares
            fund_value_dict[ticker] = pd.concat([fund_value_dict[ticker], 
                                                 pd.DataFrame([[date, net_value, shares, fund_value]], 
                                                              columns = ['date', 'net_value', 'shares', 'fund_value'])], 
                                                axis=0, ignore_index=True)
            portfolio_value = portfolio_value + fund_value

        # portfolio_value_list.append(portfolio_value)
        portfolio_value_series[date] = portfolio_value

        # 调仓，为了计算简单，在盘后即进行变更，即修改最后一行的数据
        if (i+1) % (rebalance_period) == 0: 
            for ticker in portfolio_df['ticker']:
                fund_value_df = fund_value_dict[ticker]
                target_percent = portfolio_df[portfolio_df['ticker']==ticker]['target_percent'].iloc[0]
                fund_value_change = portfolio_value * target_percent/100 - fund_value_df['fund_value'].iloc[-1]  # 正数表示有亏损，需要加仓。负数相反
                shares_change =  fund_value_change / fund_value_df['net_value'].iloc[-1]  # 正数表示需要增加份额
                fund_value_df.loc[fund_value_df.index[-1], 'shares'] += shares_change
                fund_value_df.loc[fund_value_df.index[-1], 'fund_value'] = portfolio_value * target_percent/100
                
    
    date_index = pd.date_range(start=start_date, end=end_date, freq='D')
    # portfolio_value_series = pd.Series(portfolio_value_list, index=date_index)
    max_dd, dd_peak_date, dd_bottom_date, dd_peak_value, dd_bottom_value = calculate_max_dd(portfolio_value_series)
    
    # return portfolio_value_list, max_dd, dd_peak_date, dd_bottom_date, dd_peak_value, dd_bottom_value
    return portfolio_value_series, max_dd, dd_peak_date, dd_bottom_date, dd_peak_value, dd_bottom_value

def plot(start_date, end_date, data_df):
    
    dates = pd.date_range(start=start_date, end=end_date)
    plt.figure(figsize=(12, 6))
    
    for fund_id_name in data_df.columns.tolist():
        data_list = data_df[fund_id_name].to_list()
        data_list_percent = [ (x - data_list[0])/data_list[0]*100.0 for x in data_list ]
        plt.plot(dates, data_list_percent, label=fund_id_name)
    
    plt.xlabel('时间')
    plt.ylabel('组合整体价值')
    plt.title('组合整体价值走势')
    plt.grid(True)
    plt.legend()
    plt.xticks(rotation=45)  # 旋转x轴标签以便更好地显示日期
    plt.tight_layout()

    # 显示图形
    plt.show()
    

if __name__ == "__main__":
    
    portfolio = [['163407', '兴全沪深300', 20],
         ['050025', '博时标普500', 20],
         ['000216', '华安黄金ETF', 20],
         ['000402', '工银纯债债券A', 40]]

    portfolio_df = pd.DataFrame(portfolio, columns=['ticker', 'name', 'target_percent'])

    start_date = pd.to_datetime('2015-1-1')
    end_date = pd.to_datetime('2023-11-1')
    
    rebalance_period = 90 # 调仓间隔 days
    
    # download the data and save to csv files
    # for ticker in portfolio_df['ticker']:
    #     download_and_save_fund_raw_data(ticker)
    

    # load the data from csv files and filter for this analysis
    funds_data_dict = load_potifolio_funds_data(portfolio_df['ticker'], start_date, end_date)
    
    portfolio_value_series, max_dd, dd_peak_date, dd_bottom_date, dd_peak_value, dd_bottom_value = back_trade(portfolio_df, start_date, end_date, rebalance_period, funds_data_dict)
    max_dd_percent = max_dd/dd_peak_value*100

    portfolio_profit_percent = (portfolio_value_series.iloc[-1] - portfolio_value_series.iloc[0])/portfolio_value_series.iloc[0] * 100
    years = (end_date-start_date).days / 365.0
    portfolio_profit_annual =  ((1 + portfolio_profit_percent/100) ** (1/years) - 1) * 100

    print("回测期间：{} - {}, 时长: {:.2f} 年".format(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'), years))
    print("回测期间利润: {:.2f}%, 年化利润率： {:.2f}%".format(portfolio_profit_percent, portfolio_profit_annual))    
    print("最大回撤开始日期: {}, 结束日期: {}".format(dd_peak_date.strftime('%Y-%m-%d'), dd_bottom_date.strftime('%Y-%m-%d')))
    print("最大回撤: {:.2f} - {:.2f} = {:.2f}, 回撤比例: {:.2f}%".format(dd_peak_value, dd_bottom_value, max_dd, max_dd_percent))
    
    
    plot_df = pd.DataFrame(portfolio_value_series, columns=['组合'])
    
    # for index, row in portfolio_df.iterrows():
    #     ticker = row['ticker']
    #     fund_name = row['name']
    #     fund_value_df = funds_data_dict[ticker]
    #     plot_df = plot_df.merge(funds_data_dict[ticker], left_index=True, right_index=True)
    
    plot(start_date, end_date, plot_df)
        
        
    
    
    
    
    
    # plot(start_date, end_date, [("组合", portfolio_value_list)])
    
    
    
    # df.plot()
    # plt.show()
    
    

       


    