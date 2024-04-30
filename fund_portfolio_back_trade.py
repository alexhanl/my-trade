import matplotlib.pyplot as plt
import pandas as pd

import fund_code

from fund_data_prepare_util import load_portfolio_funds_data
from fund_data_calc_util import calculate_max_dd
from fund_backtrade_util import fund_portfolio_back_trade


plt.rcParams["font.sans-serif"] = ["SimHei"]  # 设置字体
plt.rcParams["axes.unicode_minus"] = False    # 该语句解决图像中的“-”负号的乱码问题

DATA_PATH='./data'

if __name__ == "__main__":
    
    portfolio_df = pd.DataFrame(fund_code.Portfolio_LaoHuangNiu, columns=fund_code.Portfolio_Columns)
    portfolio_df.set_index('ticker', inplace=True)
    
    start_date = pd.to_datetime('2020-04-22')
    end_date = pd.to_datetime('2024-04-22')
    
    rebalance_days = 365  # 每 365 天 rebalance 一次

    portfolio_funds_data_df = load_portfolio_funds_data(portfolio_df.index, start_date, end_date)
    portfolio_value_series = fund_portfolio_back_trade(portfolio_df, start_date, end_date, rebalance_days, portfolio_funds_data_df)
    
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
    
    # 将每个列中的值改成 percent 表示
    for column_name in plt_data_df.columns:
        start_date_value = plt_data_df[column_name].iloc[0]
        plt_data_df[column_name] = (plt_data_df[column_name] - start_date_value) / start_date_value * 100
    
    plt_data_df.plot(grid=True, xlabel='时间', ylabel='价值走势', figsize=(12, 6))
    plt.tight_layout()
    plt.show()
    
    