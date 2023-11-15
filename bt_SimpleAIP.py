from datetime import datetime

import backtrader as bt

import matplotlib.pyplot as plt
import akshare as ak
import pandas as pd

from common import prepare_cn_fund_data
from fund_code import *


class SimpleAIPStrategy(bt.Strategy):   # Automatic investment plan (SIP) 基金定投，每个月的第一个交易日买入

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.dataclose = self.datas[0].close  # 指定价格序列

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None
        
        self.cash_per_month = 1000.0
        self.counter = 0
        
        self.rsi = bt.indicators.RSI_SMA(self.data.close, period=14)
 
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
            # print(dir(order.executed))
                
            self.log('CURRENT POSITION %.2f' % self.position.size)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def next(self):
        if self.order:  # 检查是否有指令等待执行,
            return
        
        assert(self.rsi, bt.indicators.rsi.RSI_SMA)
        if (self.rsi > 30):
            print(self.rsi)
        
        
        if self.counter == 12 and self.position:
            # self.order = self.sell(size=self.position.size)
            self.counter = 0
            return

        
            
        today = self.datas[0].datetime.date(ago=0)
        yesterday = self.datas[0].datetime.date(ago=-1)
        
        if (today < yesterday) or (today.month != yesterday.month):  # 是否为第一个日期，或者每月第一个交易日，实际上交易是第二个交易日的净值
            number_of_shares = self.cash_per_month / self.dataclose[0]
            self.log('BUY CREATE, Price = %.2f, Shares = %.2f' % (self.dataclose[0], number_of_shares))
            # self.order = self.buy(size=number_of_shares, exectype=bt.Order.Close)  # exectype=bt.Order.Close 以第二天的收盘价买入/卖出
            self.order = self.buy(size=number_of_shares)
            self.counter += 1
            
    

if __name__ == '__main__':

    hs300_index_data_df = ak.stock_zh_index_daily_em(symbol="sh000300").iloc[:, :6]
    hs300_index_data_df.columns = [
    'date',
    'open',
    'close',
    'high',
    'low',
    'volume',
    ]
    
    # 把 date 作为日期索引，以符合 Backtrader 的要求
    hs300_index_data_df.index = pd.to_datetime(hs300_index_data_df['date'])
    

    cerebro = bt.Cerebro()  # 初始化回测系统
    start_date = datetime(2022, 11, 1)  # 回测开始时间
    end_date = datetime(2023, 11, 1)  # 回测结束时间
    data = bt.feeds.PandasData(dataname=hs300_index_data_df, fromdate=start_date, todate=end_date)  # 加载数据

    cerebro.adddata(data)  # 将数据传入回测系统
    cerebro.addstrategy(SimpleAIPStrategy)  # 将交易策略加载到回测系统中
    start_cash = 240000
    cerebro.broker.setcash(start_cash)  # 设置初始资本为 100000
    cerebro.broker.setcommission(commission=0.00012)  # 设置交易手续费为 万分之 1.2
    # cerebro.broker.set_coc(True) # 以订单创建日的收盘价成交 cheat-on-close
    # cerebro.broker.set_checksubmit(False) # 防止下单时现金不够被拒绝。只在执行时检查现金够不够。
    
    cerebro.run()  # 运行回测系统

    port_value = cerebro.broker.getvalue()  # 获取回测结束后的总资金
    pnl = port_value - start_cash  # 盈亏统计

    print(f"初始资金: {start_cash}\n回测期间: {start_date.strftime('%Y%m%d')} - {end_date.strftime('%Y%m%d')}")
    print(f"总资金: {round(port_value, 2)}")
    print(f"净收益: {round(pnl, 2)}")
    
    cerebro.plot()

    # 结合PE
    # 结合RSI
    # 结合SAR
    