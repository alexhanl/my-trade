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

def download_and_save_fund_data(ticker: str):
    """ 利用 akshare 下载基金累计净值数据， 并且存放到data/<ticker>.csv文件中 """
    data = ak.fund_open_fund_info_em(fund=ticker, indicator="累计净值走势")
    filename = ticker + '.csv'
    data.to_csv(os.path.join(DATA_PATH, filename), index=False)

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

def load_potifolio_funds_data(ticker_series: pd.Series, start_date, end_date) -> pd.DataFrame:
    """ 获取portfolio 中每个基金的累计净值数据
    Parameters:
    ticker_series (pd.Series): 参数1的描述
    start_date
    end_date

    Returns:
    DataFrame:  like below
                163407  050025  000216  000402
    date
    2015-01-01  1.3066  1.4547  0.8980  1.0860
    2015-01-02  1.3066  1.4547  0.8980  1.0860
    2015-01-03  1.3066  1.4547  0.8980  1.0860
    2015-01-04  1.3066  1.4547  0.8980  1.0860
    2015-01-05  1.3066  1.4547  0.8980  1.0860
    ...            ...     ...     ...     ...
    2023-10-28  2.1225  3.3480  1.6984  1.5129
    2023-10-29  2.1225  3.3480  1.6984  1.5129
    2023-10-30  2.1256  3.3857  1.7028  1.5134
    2023-10-31  2.1241  3.4059  1.7027  1.5141
    2023-11-01  2.1242  3.4393  1.6976  1.5142
    """
    portfolio_funds_data_df = pd.DataFrame
    for ticker in ticker_series:
        fund_data_df = fill_non_trade_day_data(load_fund_data(ticker, start_date, end_date), start_date, end_date)  
        fund_data_df = fund_data_df.rename(columns={ACCU_NET_VALUE: ticker})
        
        if (portfolio_funds_data_df.empty):
            portfolio_funds_data_df = fund_data_df
        else:
            portfolio_funds_data_df = portfolio_funds_data_df.merge(fund_data_df, left_index=True, right_index=True)
            
    portfolio_funds_data_df = portfolio_funds_data_df.rename_axis('date')
    return portfolio_funds_data_df


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
        

def back_trade(portfolio_df, start_date, end_date, rebalance_period, portfolio_funds_data_df):
    funds_value_dict = {}  # map of fund ticker to fund_value_df  对应与excel中，每个fund一个sheet，每个sheet记录 date，net_value（当天的基金单位净值），shares（持有份额），fund_value（基金持仓价值）
    portfolio_total_value_series = pd.Series()  # portfolio_total_value_series 记录每天的portfolio的价值

    # calculate the initial number of shares, fund value and total fund value
    start_date_net_value_series = portfolio_funds_data_df.iloc[0]
    # print(start_date_net_value_series)
    for ticker, target_percent in portfolio_df['target_percent'].items():
        start_date_net_value = start_date_net_value_series[ticker]
        fund_value = TOTAL_INVESTMENT * target_percent / 100 
        shares = fund_value / start_date_net_value
        funds_value_dict[ticker] = pd.DataFrame([[start_date, start_date_net_value, shares, fund_value]], 
                                               columns=['date', 'net_value', 'shares', 'fund_value'])

    # 计算start_date的初始 portfolio 整体 value，在没有佣金的情况下，应该为 TOTAL_INVESTMENT，也就是100
    portfolio_value = 0.0 
    for ticker in portfolio_df.index:
        portfolio_value = portfolio_value + funds_value_dict[ticker]['fund_value'].iloc[0]

    portfolio_total_value_series[start_date] = portfolio_value

    # 计算每天的基金价值变化，从第二天开始
    day_counter = 0
    for date, funds_net_value in portfolio_funds_data_df.iloc[1:].iterrows():
        day_counter = day_counter + 1
        portfolio_value = 0.0
        for ticker in portfolio_df.index:
            net_value = funds_net_value[ticker]
            shares = funds_value_dict[ticker]['shares'].iloc[-1]  # 在没有交易的情况下，基金份额保持不变
            fund_value = net_value * shares
            funds_value_dict[ticker] = pd.concat([funds_value_dict[ticker], 
                                                 pd.DataFrame([[date, net_value, shares, fund_value]], 
                                                              columns = ['date', 'net_value', 'shares', 'fund_value'])], 
                                                axis=0, ignore_index=True)
            portfolio_value = portfolio_value + fund_value

        # portfolio_value_list.append(portfolio_value)
        portfolio_total_value_series[date] = portfolio_value
        
        # 重平衡，为了计算简单，直接在盘后即进行变更，并修正最后一行的数据（即当天的数据）
        if day_counter % rebalance_period == 0: 
            for ticker in portfolio_df.index:
                fund_value_df = funds_value_dict[ticker]
                target_percent = portfolio_df.loc[ticker, 'target_percent']
                fund_value_change = portfolio_value * target_percent/100 - fund_value_df['fund_value'].iloc[-1]  # 正数表示有亏损，需要加仓。负数相反
                shares_change =  fund_value_change / fund_value_df['net_value'].iloc[-1]  # 正数表示需要增加份额
                fund_value_df.loc[fund_value_df.index[-1], 'shares'] += shares_change
                fund_value_df.loc[fund_value_df.index[-1], 'fund_value'] = portfolio_value * target_percent/100
        
    max_dd, dd_peak_date, dd_bottom_date, dd_peak_value, dd_bottom_value = calculate_max_dd(portfolio_total_value_series)
    
    return portfolio_total_value_series, max_dd, dd_peak_date, dd_bottom_date, dd_peak_value, dd_bottom_value


    

if __name__ == "__main__":
    
    portfolio = [
        ['163407', '兴全沪深300', 20],
        # ['110020', '易方达沪深300ETF连接', 20],
        ['050025', '博时标普500', 20],
        ['000216', '华安黄金ETF', 20],
        ['000402', '工银纯债债券A', 40]
        ]

    portfolio_df = pd.DataFrame(portfolio, columns=['ticker', 'name', 'target_percent'])
    portfolio_df.set_index('ticker', inplace=True)
    
    start_date = pd.to_datetime('2014-11-10')
    end_date = pd.to_datetime('2023-11-10')
    
    rebalance_period = 90 #000000000 # 调仓间隔 days
    
    # download the data and save to csv files
    # for ticker in portfolio_df.index:
    #     download_and_save_fund_raw_data(ticker)

    portfolio_funds_data_df = load_potifolio_funds_data(portfolio_df.index, start_date, end_date)
    
    portfolio_value_series, max_dd, dd_peak_date, dd_bottom_date, dd_peak_value, dd_bottom_value = back_trade(portfolio_df, start_date, end_date, rebalance_period, portfolio_funds_data_df)
    max_dd_percent = max_dd/dd_peak_value*100

    portfolio_profit_percent = (portfolio_value_series.iloc[-1] - portfolio_value_series.iloc[0])/portfolio_value_series.iloc[0] * 100
    years = (end_date-start_date).days / 365.0
    portfolio_profit_annual =  ((1 + portfolio_profit_percent/100) ** (1/years) - 1) * 100

    print("回测期间：{} - {}, 时长: {:.2f} 年".format(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'), years))
    print("回测期间利润: {:.2f}%, 年化利润率： {:.2f}%".format(portfolio_profit_percent, portfolio_profit_annual))    
    print("最大回撤开始日期: {}, 结束日期: {}".format(dd_peak_date.strftime('%Y-%m-%d'), dd_bottom_date.strftime('%Y-%m-%d')))
    print("最大回撤: {:.2f} - {:.2f} = {:.2f}, 回撤比例: {:.2f}%".format(dd_peak_value, dd_bottom_value, max_dd, max_dd_percent))
    
    print("组合成员的情况：")
    for ticker in portfolio_funds_data_df.columns:
        start_value = portfolio_funds_data_df[ticker].iloc[0]
        end_value = portfolio_funds_data_df[ticker].iloc[-1]
        profit_percent = (end_value - start_value)/start_value * 100
        annaulized_profit_percent = ((1 + profit_percent/100) ** (1/years) - 1) * 100
        max_dd, dd_peak_date, dd_bottom_date, dd_peak_value, dd_bottom_value = calculate_max_dd(portfolio_funds_data_df[ticker])
        max_dd_percent = max_dd/dd_peak_value*100
        print("{} {}: 利润 {:.2f}%, 年化：{:.2f}%, 最大回撤：{:.2f}%".format(ticker, portfolio_df.loc[ticker, 'name'], profit_percent, annaulized_profit_percent, max_dd_percent))
    
    
       
    # 展示图
    plt_data_df = portfolio_funds_data_df
    for ticker in plt_data_df.columns:
        plt_data_df = plt_data_df.rename(columns={ticker: ticker + portfolio_df.loc[ticker, 'name']})    
    plt_data_df['投资组合'] = portfolio_value_series
    
    # 讲每个列中的值改成 percent 表示
    for column_name in plt_data_df.columns:
        start_date_value = plt_data_df[column_name].iloc[0]
        plt_data_df[column_name] = (plt_data_df[column_name] - start_date_value) / start_date_value * 100
    
    plt_data_df.plot(grid=True, xlabel='时间', ylabel='价值走势', figsize=(12, 6))
    plt.tight_layout()
    plt.show()
    
       


    