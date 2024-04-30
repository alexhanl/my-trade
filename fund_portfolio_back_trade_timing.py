import matplotlib.pyplot as plt
import pandas as pd
import multiprocessing
import statistics

import fund_code
from fund_data_prepare_util import load_portfolio_funds_data
from fund_backtrade_util import calculate_max_dd, fund_portfolio_back_trade

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

DATA_PATH = './data'

def backtrade(portfolio_df, start_date, end_date):
    rebalance_days = 220  # 每 220 个交易日 rebalance 一次
    portfolio_funds_data_df = load_portfolio_funds_data(portfolio_df.index, start_date, end_date).ffill().bfill()  # 使用 bfill() 是为了防止第一行数据出现空值
    portfolio_value_series = fund_portfolio_back_trade(portfolio_df, portfolio_funds_data_df, rebalance_days)

    portfolio_profit_percent = (portfolio_value_series.iloc[-1] - portfolio_value_series.iloc[0]) / portfolio_value_series.iloc[0] * 100
    years = (end_date - start_date).days / 365.0
    portfolio_profit_annual = ((1 + portfolio_profit_percent / 100) ** (1 / years) - 1) * 100
    
    return portfolio_profit_annual


def print_statistics(profits):
    
    
    
    # 计算平均值
    mean_profit = statistics.mean(profits)  # 平均值
    print("平均收益是:", mean_profit, "%")  # 注意这里要乘以100，因为收益是百分比形式
    
    min_profit = min(profits)  # 最小值
    max_profit = max(profits)  # 最大值
    print("最小收益是:", min_profit, "%")  # 注意这里要乘以100，因为收益是百分比形式
    print("最大收益是:", max_profit, "%")  # 注意这里要乘以100，因为收益是百分比形式
    print("最大收益相对于平均收益：", max_profit / mean_profit, "倍")  # 注意这里要乘以100，因为收益是百分比形式
    print("最大收益相对于最小收益：", max_profit / min_profit, "倍")  # 注意这里要乘以100，因为收益是百分比形式
    
    # 计算标准差
    std_dev = statistics.stdev(profits)
    print("标准差是:", std_dev)

    # 计算方差
    variance = statistics.variance(profits)
    print("方差是:", variance)

    

def plot_data(profits):
     # 绘制直方图
    plt.figure(figsize=(10, 6))
    plt.subplot(2, 1, 1)  # 第一个子图
    sns.histplot(profits, kde=True, bins=8)  # 使用Seaborn绘制直方图和KDE曲线
    plt.title('Histogram with KDE')

    # 绘制箱形图
    plt.subplot(2, 1, 2)  # 第二个子图
    sns.boxplot(x=profits)
    plt.title('Boxplot')

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    portfolio_df = pd.DataFrame(fund_code.Portfolio_LaoHuangNiu, columns=fund_code.Portfolio_Columns)
    portfolio_df.set_index('ticker', inplace=True)
    
    end_date = pd.to_datetime('2024-04-22')
    # end_dates = pd.date_range(end_date - pd.DateOffset(months=48), end_date, freq='M')
    # start_dates = end_dates - pd.DateOffset(years=5)  # 计算开始日期，即结束日期减去5年
    
    start_dates = pd.date_range(pd.to_datetime('2015-01-02'), end_date-pd.DateOffset(years=5), freq='M')
    
    print(start_dates)
    
    
    profits = []
    
    with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
        args = [(portfolio_df, start, end_date) for start in start_dates]
        results = pool.starmap(backtrade, args)
        profits.extend(results)
    
    print(profits)
    
    # profits = [6.282227734317503, 6.3695159855199135, 7.333433509488629, 9.063016346018028, 9.234762387440988, 9.272264245218853, 8.286978345165629, 8.893005106364061, 9.018246759828008, 10.1979223393182, 9.621327708363815, 8.998675737023643, 9.135995312534817, 9.620974744372068, 8.884194431507764, 8.743410852862322, 8.764684383336885, 8.69146870070412, 8.884666291006326, 8.591481310047367, 9.095467412866821, 8.230604555903586, 8.065008995677637, 8.10448707002367, 7.679704608326143, 7.656467061575012, 7.500406266843784, 7.363767543028876, 7.266452028578585, 6.409890091787918, 6.469891038283793, 6.999464575569703, 6.824571802061152, 7.07628035067005, 7.371276380742886, 8.01553538297508, 8.230958534502841, 8.155532466912675, 8.528355386938792, 8.378583218790547, 8.318633083065041, 7.94531375813845, 8.210982709875925, 8.40468549412956, 9.089577994038823, 8.596534515115707, 8.363944441491643, 8.549198344628927]
    
    # 以 start_dates 为x轴，profits 为 y轴，通过 matplot lib 绘制折线图，并添加标题和标签。
    plt.plot(start_dates, profits, marker='o')  # 绘制折线图，并使用圆形标记点
    plt.show()
    
    print_statistics(profits)
    
    # plot_data(profits)


