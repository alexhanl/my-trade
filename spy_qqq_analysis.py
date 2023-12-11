from datetime import datetime, timedelta
import matplotlib.ticker as ticker
import backtrader as bt

import matplotlib.pyplot as plt
import akshare as ak
import pandas as pd

import os

DATA_PATH = './data'

today = datetime(2023,11,24)  ## datetime.now().date()   #.strftime('%Y-%m-%d')

ten_years_ago = today - timedelta(days=10*365)
five_years_ago = today - timedelta(days=5*365)
three_yeas_ago = today - timedelta(days=3*365)
one_year_ago = today - timedelta(days=365)


def calc(data_df, years, interval):
    start_date = today - timedelta(days=years*365)
    end_date = today
    data_df = data_df[(data_df.index >= pd.to_datetime(start_date)) & (data_df.index <= pd.to_datetime(end_date))]
    
    closes_list = data_df['close'].to_list()
    fng_list = data_df['fear_greed'].to_list()
    rsi_list = data_df['rsi'].to_list()
    psar_list = data_df['psar'].to_list()
    dates_list = data_df.index
    profits = []
    buying_dates_win = pd.Series()
    buying_dates_lose = pd.Series()
    
    signal_tag = 0
    
    for i in range(len(closes_list) - interval):
        
        # if (fng_list[i] >= 75):
        # if (fng_list[i] <= 25):
        # if (rsi_list[i] >= 70):
        # if (rsi_list[i] <= 30):
        
        # if (psar_list[i] < closes_list[i]): # psar 买入信号
        if (psar_list[i] > closes_list[i]): # psar 卖出信号
            signal_tag = signal_tag + 1
            if (signal_tag == 2) : # & (rsi_list[i] > 60) :
                profit_rate = (closes_list[i+interval] - closes_list[i])/closes_list[i]
                profits.append(profit_rate)
                if profit_rate > 0:
                    buying_dates_win[dates_list[i]] = closes_list[i]
                else:
                    buying_dates_lose[dates_list[i]] = closes_list[i]
                print('买入时间：{}  当天价格：{:.2f} 当天恐贪指数{} rsi {}, {}交易日后 {} 价格: {:.2f}, 收益率为 {:.2f}%'.format(
                    dates_list[i].strftime('%Y-%m-%d'), closes_list[i], fng_list[i], rsi_list[i], interval, dates_list[i+interval].strftime('%Y-%m-%d'), closes_list[i+interval], profit_rate*100) )
        else:
            signal_tag = 0
        
    average_profit = sum(profits)/len(profits)
    
    positive_profit_list = [i for i in profits if i >= 0]    
    negative_profit_list = [i for i in profits if i < 0] 
    
    positive_days = len(positive_profit_list)
    # negative_days = len(negative_profit_list)
    
    max_loss = min(profits)
    max_win = max(profits)
    
    print("{}年内，买点出现次数:{}, {}个交易日内，平均利润：{:.2f}%, 盈利概率: {:.2f}%, 最大盈利：{:.2f}%, 最大损失：{:.2f}%".format(
        years, len(profits), interval, average_profit*100, positive_days/len(profits)*100, max_win*100, max_loss*100))
    
    data_s = data_df['close']
    psar_s = data_df['psar']
    
    plt.scatter(buying_dates_win.index, buying_dates_win, marker='^', color='red', s=40)
    plt.scatter(buying_dates_lose.index, buying_dates_lose, marker='v', color='green', s=40)
    
    data_s.plot()
    plt.scatter(psar_s.index, psar_s, marker='o', s=3, color='grey')   
    plt.show()
    



if __name__ == '__main__':
    
    data_df = pd.read_csv(os.path.join(DATA_PATH, 'qqq.csv'))
    data_df['date'] = pd.to_datetime(data_df['date'], format='%Y-%m-%d') 
    data_df.set_index('date', inplace=True)
        
    fear_greed_index_df = pd.read_csv(os.path.join(DATA_PATH, 'all_fng_csv.csv'))
    fear_greed_index_df.rename(columns={'Date': 'date'}, inplace=True)
    fear_greed_index_df['date'] = pd.to_datetime(fear_greed_index_df['date'], format='%Y-%m-%d') 
    fear_greed_index_df.set_index('date', inplace=True)
    data_df['fear_greed'] = fear_greed_index_df['Fear Greed']
    
    psar_df = pd.read_csv(os.path.join(DATA_PATH, 'qqq_psar.csv'))
    psar_df['date'] = pd.to_datetime(psar_df['date'], format='%Y-%m-%d') 
    psar_df.set_index('date', inplace=True)
    data_df['psar'] = psar_df['psar']

    years_options = [3]
    interval_options = [8]
    
    for interval in interval_options:
        for years in years_options:
            calc(data_df=data_df, years=years, interval=interval)
    
            
    # data_df_plot = pd.DataFrame()
    # data_df_plot.index = data_df.index
    # plt.show()
            
    
    
# 平均    
# 5年，买点出现次数:1251, 7个交易日内，平均利润：0.34%, 盈利概率: 61.07%, 最大盈利：12.69%, 最大损失：-20.70%
# 5年，买点出现次数:1236, 22个交易日内，平均利润：1.09%, 盈利概率: 66.18%, 最大盈利：25.18%, 最大损失：-33.83%
    
# 恐贪指数 <= 25 时买入
# 5年，买点出现次数:204, 7个交易日内，平均利润：0.74%, 盈利概率: 64.22%, 最大盈利：12.69%, 最大损失：-20.70%
# 5年，买点出现次数:201, 22个交易日内，平均利润：3.18%, 盈利概率: 72.64%, 最大盈利：25.18%, 最大损失：-20.67%  
   
# 恐贪指数 >= 75 时买入 
# 5年，买点出现次数:95, 7个交易日内，平均利润：0.28%, 盈利概率: 66.32%, 最大盈利：3.57%, 最大损失：-5.38%
# 5年，买点出现次数:95, 22个交易日内，平均利润：0.99%, 盈利概率: 72.63%, 最大盈利：5.15%, 最大损失：-7.05%
    
# RSI <= 30 时买入
# 5年，买点出现次数:23, 7个交易日内，平均利润：0.66%, 盈利概率: 69.57%, 最大盈利：10.41%, 最大损失：-12.48%
# 5年，买点出现次数:22, 22个交易日内，平均利润：1.70%, 盈利概率: 63.64%, 最大盈利：25.18%, 最大损失：-18.65%
    
# RSI >= 70 时买入
# 5年，买点出现次数:81, 7个交易日内，平均利润：-0.61%, 盈利概率: 46.91%, 最大盈利：4.31%, 最大损失：-5.38%
# 5年，买点出现次数:81, 22个交易日内，平均利润：-0.57%, 盈利概率: 51.85%, 最大盈利：3.90%, 最大损失：-10.27%

# psar 买入信号
# 5年，买点出现次数:780, 7个交易日内，平均利润：0.44%, 盈利概率: 63.08%, 最大盈利：12.69%, 最大损失：-12.44%
# 5年，买点出现次数:771, 22个交易日内，平均利润：0.81%, 盈利概率: 66.15%, 最大盈利：16.31%, 最大损失：-33.83%

# psar 买入信号首次出现时买入
# 5年，买点出现次数:51, 7个交易日内，平均利润：0.29%, 盈利概率: 62.75%, 最大盈利：4.41%, 最大损失：-6.37%
# 5年，买点出现次数:50, 22个交易日内，平均利润：1.32%, 盈利概率: 66.00%, 最大盈利：16.31%, 最大损失：-17.61%

# psar 卖出信号
# 5年，买点出现次数:471, 7个交易日内，平均利润：0.16%, 盈利概率: 57.75%, 最大盈利：12.65%, 最大损失：-20.70%
# 5年，买点出现次数:465, 22个交易日内，平均利润：1.55%, 盈利概率: 66.24%, 最大盈利：25.18%, 最大损失：-23.46%

# psar 卖出信号首次出现时买入
# 5年，买点出现次数:51, 7个交易日内，平均利润：-0.22%, 盈利概率: 49.02%, 最大盈利：4.91%, 最大损失：-6.62%
# 5年，买点出现次数:51, 22个交易日内，平均利润：0.23%, 盈利概率: 56.86%, 最大盈利：10.39%, 最大损失：-23.46%
