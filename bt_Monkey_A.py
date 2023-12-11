from datetime import datetime

import backtrader as bt

import matplotlib.pyplot as plt
import akshare as ak
import pandas as pd

from common import prepare_cn_fund_data
from fund_code import *
import os

class MonkeyStrategy(bt.Strategy):

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))
        
        
    def __init__(self):
        self.close_price = self.datas[0].close  # 指定价格序列
        
        self.psar = bt.ind.ParabolicSAR(period=20, af = 0.015)
        # self.sma = bt.indicators.SimpleMovingAverage(self.data)
        self.rsi = bt.indicators.RSI_Safe(self.data.close, period=14)
        
        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None
        
        self.buy_signal = 0
        self.sell_signal = 0
        
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

    def check_signals(self): 
                
        # if self.rsi[0] < 30:
        #     return 1
        # elif self.rsi[0] > 70:
        #     return -1
        
        if self.psar[0] < self.close_price[0]:
            return 1
            self.sell_signal = 0
            if self.buy_signal == 1:
                self.buy_signal = 0
                return 1
            else:
                self.buy_signal = self.buy_signal + 1
        elif self.psar[0] > self.close_price[0]:
            return -1
            self.buy_signal = 0
            if self.sell_signal == 1:
                self.sell_signal = 0
                return -1
            else:
                self.sell_signal = self.sell_signal + 1    
        return 0
    
    
    
    def next(self):
        if self.order:  # 检查是否有指令等待执行,
            return
        
        # self.log('Close: {:.2f}, RSI:  {:.2f}'.format(self.close_price[0], self.rsi[0]))
        
        signal = self.check_signals()
        
        if signal == 1:
            size = int(cerebro.broker.get_cash() / self.close_price[0]) -1
            if size > 0:
                self.log('Indicators for BUY: RSI: %.2f' % (self.rsi[0]))
                self.log('BUY CREATE, Price = %.2f, Shares = %.2f' % (self.close_price[0], size))
                self.order = self.buy(size=size)
        elif signal == -1 and self.position.size > 0:
            self.log('Indicators for SELL: RSI: %.2f' % (self.rsi[0]))
            self.log('SELL CREATE, Price = %.2f, Shares = %.2f' % (self.close_price[0], self.position.size))
            self.order = self.sell(size=self.position.size)

    
DATA_PATH='./data'

class CustomPandasData(bt.feeds.PandasData):
    lines = ('rsi',)
    params = (('rsi', -1), )
    plotinfo = {"plot": True, "subplot": True}
        
if __name__ == '__main__':
    data_df = ak.stock_zh_index_daily_em(symbol="sh000300").iloc[:, :6]
    data_df.columns = [
    'date',
    'open',
    'close',
    'high',
    'low',
    'volume',
    ]
    
    # 把 date 作为日期索引，以符合 Backtrader 的要求
    data_df.index = pd.to_datetime(data_df['date'])
    
    cerebro = bt.Cerebro()  # 初始化回测系统
    # cerebro = bt.Cerebro(stdstats=False)
    start_date = datetime(2018, 11, 16)  # 回测开始时间
    end_date = datetime(2023, 11, 16)  # 回测结束时间
    
    data = CustomPandasData(dataname=data_df, fromdate=start_date, todate=end_date, rsi=5)

    cerebro.adddata(data)
    
    cerebro.addstrategy(MonkeyStrategy)  # 将交易策略加载到回测系统中
    start_cash = 1000000
    cerebro.broker.setcash(start_cash)  # 设置初始资本为 1,000,000
    cerebro.broker.setcommission(commission=0.00012)  # 设置交易手续费为 万分之 1.2
    cerebro.broker.set_coc(True) # 以订单创建日的收盘价成交 cheat-on-close
            
    cerebro.addobserver(bt.observers.Value)
    cerebro.addobserver(bt.observers.BuySell)
    # cerebro.addobserver(bt.observers.DrawDown)
    
    
    cerebro.run(stdstats=False)  # 运行回测系统
    
    # assert(broker, bt.brokers.bbroker.BackBroker)    

    port_value = cerebro.broker.getvalue()  # 获取回测结束后的总资金
    pnl = port_value - start_cash  # 盈亏统计

    print(f"初始资金: {start_cash}\n回测期间: {start_date.strftime('%Y%m%d')} - {end_date.strftime('%Y%m%d')}")
    print(f"总资金: {round(port_value, 2)}")
    print(f"净收益: {round(pnl, 2)}")
    
    start_price = data_df['close'][start_date]
    end_price = data_df['close'][end_date]
    print('市场标普500, 起始日: {:.2f}, 结束日：{:.2f}, 涨幅：{:.2f}%  '.format(start_price, end_price, (end_price/start_price-1)*100))
    
    
    cerebro.plot()


    