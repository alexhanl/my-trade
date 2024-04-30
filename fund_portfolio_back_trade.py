import matplotlib.pyplot as plt
import pandas as pd

from data_prepare_util import load_portfolio_funds_data
from data_calc_util import calculate_max_dd

plt.rcParams["font.sans-serif"] = ["SimHei"]  # 设置字体
plt.rcParams["axes.unicode_minus"] = False    # 该语句解决图像中的“-”负号的乱码问题

TOTAL_INVESTMENT = 100.0
DATA_PATH='./data'

def back_trade(portfolio_df, start_date, end_date, rebalance_period, portfolio_funds_data_df):
    funds_value_dict = {}  # map of fund ticker to fund_value_df  对应与excel中，每个fund一个sheet，每个sheet记录 date，net_value（当天的基金单位净值），shares（持有份额），fund_value（基金持仓价值）
    portfolio_value_series = pd.Series()  # portfolio_total_value_series 记录每天的portfolio的价值

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
    current_portfolio_value = sum(funds_value_dict[ticker]['fund_value'].iloc[0] for ticker in portfolio_df.index)

    portfolio_value_series[start_date] = current_portfolio_value

    # 计算每天的基金价值变化，从第二天开始
    day_counter = 0
    for date, funds_net_value in portfolio_funds_data_df.iloc[1:].iterrows():
        day_counter = day_counter + 1
        current_portfolio_value = 0.0
        for ticker in portfolio_df.index:
            net_value = funds_net_value[ticker]
            shares = funds_value_dict[ticker]['shares'].iloc[-1]  # 在没有交易的情况下，基金份额保持不变，直接获取上一日的数据即可
            fund_value = net_value * shares
            funds_value_dict[ticker] = pd.concat([funds_value_dict[ticker], 
                                                 pd.DataFrame([[date, net_value, shares, fund_value]], 
                                                              columns = ['date', 'net_value', 'shares', 'fund_value'])], 
                                                axis=0, ignore_index=True)
            current_portfolio_value = current_portfolio_value + fund_value

        portfolio_value_series[date] = current_portfolio_value
        
        # 重平衡，为了计算简单，直接在盘后即进行变更，并修正最后一行的数据（即当天的数据）
        if day_counter % rebalance_period == 0: 
            # print("---- 阶段业绩：  {} - {} ----".format( (date - pd.Timedelta(days=rebalance_period)).date(), date.date()))
            for ticker in portfolio_df.index:
                fund_value_df = funds_value_dict[ticker]
                target_percent = portfolio_df.loc[ticker, 'target_percent']
                fund_value_change = current_portfolio_value * target_percent/100 - fund_value_df['fund_value'].iloc[-1]  # 正数表示未达到target_percent，需要加仓。负数相反
                
                # fund_name = portfolio_df.loc[ticker, 'name']
                # profit = fund_value_df['fund_value'].iloc[-1] - fund_value_df['fund_value'].iloc[-rebalance_period]
                # print("{} 利润比例为 {:.2f} %".format(fund_name, profit/fund_value_df['fund_value'].iloc[-rebalance_period] * 100))
                
                shares_change =  fund_value_change / fund_value_df['net_value'].iloc[-1]  # 正数表示需要增加份额
                fund_value_df.loc[fund_value_df.index[-1], 'shares'] += shares_change
                fund_value_df.loc[fund_value_df.index[-1], 'fund_value'] = current_portfolio_value * target_percent/100
    
    return portfolio_value_series


if __name__ == "__main__":
    
    portfolio = [
        ['000368', '汇添富沪深300安中指数A', 20],  
        ['050025', '博时标普500', 20],
        ['000216', '华安黄金ETF', 20],
        ['400030', '东方天益', 8], 
        ['000914', '中加纯债', 8],  
        ['004388', '鹏华债券', 8], 
        ['000032', '易方达信用债', 8],
        ['000187', '华泰博瑞', 8]
    ]

    portfolio_df = pd.DataFrame(portfolio, columns=['ticker', 'name', 'target_percent'])
    portfolio_df.set_index('ticker', inplace=True)
    
    start_date = pd.to_datetime('2020-04-22')
    end_date = pd.to_datetime('2024-04-22')
    
    rebalance_days = 365  # 每 365 天 rebalance 一次

    portfolio_funds_data_df = load_portfolio_funds_data(portfolio_df.index, start_date, end_date)
    portfolio_value_series = back_trade(portfolio_df, start_date, end_date, rebalance_days, portfolio_funds_data_df)
    
    # 计算相关 KPI，并展示结果
    max_dd, dd_peak_date, dd_bottom_date, dd_peak_value, dd_bottom_value = calculate_max_dd(portfolio_value_series)
    max_dd_percent = max_dd/dd_peak_value*100

    portfolio_profit_percent = (portfolio_value_series.iloc[-1] - portfolio_value_series.iloc[0])/portfolio_value_series.iloc[0] * 100
    years = (end_date-start_date).days / 365.0
    portfolio_profit_annual =  ((1 + portfolio_profit_percent/100) ** (1/years) - 1) * 100

    print("回测期间：{} - {}, 时长: {:.2f} 年".format(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'), years))
    print("回测期间利润: {:.2f}%, 年化利润率： {:.2f}%".format(portfolio_profit_percent, portfolio_profit_annual))    
    print("最大回撤开始日期: {}, 结束日期: {}, 持续 {} 天".format(dd_peak_date.strftime('%Y-%m-%d'), dd_bottom_date.strftime('%Y-%m-%d'), (dd_bottom_date-dd_peak_date).days))
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
       
    # 展示曲线图
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
    
       


    