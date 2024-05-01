import backtrader as bt
import matplotlib.pyplot as plt
import akshare as ak
import pandas as pd
import os

from datetime import datetime, timedelta
from common import Loglevel
from common import MyDrawDown

DATA_PATH='./data'

class MyStrategy(bt.Strategy):

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        # print('%s, %s' % (dt.isoformat(), txt))        
        
    def __init__(self):
        self.close_price = self.datas[0].close  # 指定价格序列
        
        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None
        
        self.cash_per_month = 100000
        
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Shares: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price, 
                     order.executed.size,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Shares: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.size,
                          order.executed.value,
                          order.executed.comm))
                
            # self.log('CURRENT POSITION %.2f' % self.position.size)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    
    def all_in(self):
        size = int(self.broker.get_cash() / self.close_price[0])
        if size > 0:
            self.log('BUY CREATE, Price = %.2f, Shares = %.2f' % (self.close_price[0], size))
            self.order = self.buy(size=size)
    
    def close_position(self):
        self.log('SELL CREATE, Price = %.2f, Shares = %.2f' % (self.close_price[0], self.position.size))
        self.order = self.sell(size=self.position.size)
    
    
    def isFirstTradingDay(self):
        today = self.datas[0].datetime.date(ago=0)
        yesterday = self.datas[0].datetime.date(ago=-1)
        
        if (today > yesterday) and (today.month != yesterday.month):  # 是否为每月第一个交易日
            return True
        else:
            return False    
    
    
    def next(self):
        if self.order:  # 检查是否有指令等待执行,
            return
        
        if self.isFirstTradingDay():
            number_of_shares = self.cash_per_month / self.close_price[0]
            self.log('BUY CREATE, Price = %.2f, Shares = %.2f' % (self.close_price[0], number_of_shares))
            self.order = self.buy(size=number_of_shares)

def calc_rate(positions, cash_per_month, last_price):
    total_value = last_price * sum(positions) 
    total_invest = cash_per_month * len(positions)
    profit_rate = (total_value - total_invest) / total_invest * 100
    return profit_rate

def run_strategy(ticker: str, start_date, end_date):
    data_df = pd.read_csv(os.path.join(DATA_PATH, ticker + '.csv'))
    data_df['date'] = pd.to_datetime(data_df['date'], format='%Y-%m-%d') 
    data_df = data_df[(data_df.date >= start_date) & (data_df.date <= end_date)]
    dates = data_df['date'].to_list()
    closes = data_df['close'].to_list()
    
    print('{} - {}:\t'.format(start_date.strftime('%Y%m%d'), end_date.strftime('%Y%m%d')), end="")
    
    cash_per_month = 10000
    profit_rates = []
    
    # 每月第一天
    # positions = []
    # for i in range(1, len(dates)):
    #     today = dates[i]
    #     yesterday = dates[i-1]
    #     if (today.month != yesterday.month): 
    #         positions.append(cash_per_month/closes[i])
    # profit_rates.append(calc_rate(positions, cash_per_month, closes[-1]))
    
    # 每月第二天
    # positions = []
    # for i in range(2, len(dates)):
    #     today = dates[i]
    #     yesteraday = dates[i-1]
    #     the_day_before_yesterday = dates[i-2]
    #     if (today.month == yesteraday.month) and (yesteraday.month != the_day_before_yesterday.month): 
    #         positions.append(cash_per_month/closes[i])
    # profit_rates.append(calc_rate(positions, cash_per_month, closes[-1]))
    
    # # 每月最后一天
    # positions = []
    # for j in range(0, len(dates)-1):
    #     today = dates[j]
    #     tomorrow = dates[j+1]
    #     if (today.month != tomorrow.month):
    #         positions.append(cash_per_month/closes[j])
    # profit_rates.append(calc_rate(positions, cash_per_month, closes[-1]))
    
    # 每月倒数第二天
    # positions = []
    # for j in range(0, len(dates)-2):
    #     today = dates[j]
    #     tomorrow = dates[j+1]
    #     the_day_after_tomorrow = dates[j+2]
    #     if (today.month == tomorrow.month) and (tomorrow.month != the_day_after_tomorrow.month):
    #         positions.append(cash_per_month/closes[j])
    # profit_rates.append(calc_rate(positions, cash_per_month, closes[-1]))
    
    
    # print("\t".join("{:.2f}".format(x) for x in profit_rates))
    # print("{:.2f}\t{:.2f}\t{:.2f}".format(profit_rates[0],profit_rates[1],profit_rates[1] - profit_rates[0]))
  
    
    
def run_backtrade():
    end_date = datetime(2023,11,24)
    start_date = datetime(2013,11,24)
    
    data_df = pd.read_csv(os.path.join(DATA_PATH, 'qqq.csv'))
    data_df['date'] = pd.to_datetime(data_df['date'], format='%Y-%m-%d') 
    # data_df['date'] = pd.to_datetime(data_df['date'], format='%Y/%m/%d')
    
    data_df = data_df[(data_df.date >= start_date) & (data_df.date <= end_date)]
    dates = data_df['date'].to_list()
    closes = data_df['close'].to_list()
    
    cash_per_month = 1000
    
    day_of_the_month = [1, 28, 30]
    
    
    
    
    
    
    
    
    gap = []
    for i in range(1, len(dates)):
        today = dates[i]
        yesterday = dates[i-1]
        if (today.month != yesterday.month): 
            month_head = closes[i+4] - closes[i-1]
            month_tail = closes[i] - closes[i-5]
            gap.append(month_head - month_tail)
            # gap.append(month_tail)
    
    positives =  [x for x in gap if x > 0]     
    negatives =  [x for x in gap if x < 0]     
    print(len(positives))
    print(len(negatives))
       
       
    # for i in range(0, 18):
    #     end_date = full_period[1] - timedelta(days=i*365)
    #     start_date = end_date - timedelta(days=2*365)
    #     run_strategy(ticker='qqq', start_date=start_date, end_date=end_date)
    
    
if __name__ == '__main__':
    run_backtrade()
