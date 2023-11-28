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
        # self.dataclose = self.datas[0].close  # 指定价格序列
        self.close_price = self.getdatabyname('stock_price').close
        self.rsi = self.getdatabyname('stock_rsi').close
        self.fear_greed = self.getdatabyname('fear_greed_index').close

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None
        
        # self.rsi = bt.indicators.RSI_Safe(self.data.close, period=14)
        
        
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

    def next(self):
        if self.order:  # 检查是否有指令等待执行,
            return
        
        # assert(self.rsi, bt.indicators.rsi.RSI_SAFE)
        
        if self.fear_greed < 25:
            size = int(cerebro.broker.get_cash() / self.close_price[0]) -1
            if size > 0:
                self.log('BUY CREATE, Price = %.2f, Shares = %.2f' % (self.close_price[0], size))
                self.order = self.buy(size=size)
        elif self.fear_greed > 75 and self.position.size > 0:
            self.log('Price: %.2f, RSI: %.2f, Fear_Greed: %.2f' % (self.close_price[0], self.rsi[0], self.fear_greed[0]))
            self.log('SELL CREATE, Price = %.2f, Shares = %.2f' % (self.close_price[0], self.position.size))
            self.order = self.sell(size=self.position.size)



class ValueTracker(bt.Observer):
    lines = ('value',)

    def next(self):
        self.lines.value[0] = self._owner.broker.getvalue()
    
DATA_PATH='./data'

if __name__ == '__main__':
    
    ticker = 'spy'
    spy_data_df = pd.read_csv(os.path.join(DATA_PATH, ticker + '.csv'))
    spy_data_df['date'] = pd.to_datetime(spy_data_df['date'], format='%Y-%m-%d') 
    spy_data_df.set_index('date', inplace=True)
    
    spy_price_data_df = spy_data_df[['open', 'high', 'low', 'close', 'volume']].copy()
    
    spy_rsi_data_df = spy_data_df[['rsi']].copy()
    spy_rsi_data_df.rename(columns={'rsi': 'close'}, inplace=True)
    
    fear_greed_index_df = pd.read_csv(os.path.join(DATA_PATH, 'all_fng_csv.csv'))
    fear_greed_index_df.rename(columns={'Date': 'date', 'Fear Greed': 'close'}, inplace=True)
    fear_greed_index_df['date'] = pd.to_datetime(fear_greed_index_df['date'], format='%Y-%m-%d') 
    fear_greed_index_df.set_index('date', inplace=True)
    
    
    
    
    
    

    cerebro = bt.Cerebro()  # 初始化回测系统
    # cerebro = bt.Cerebro(stdstats=False)  # 初始化回测系统
    start_date = datetime(2023, 1, 30)  # 回测开始时间
    end_date = datetime(2023, 10, 30)  # 回测结束时间
    
    stock_price_data = bt.feeds.PandasData(dataname=spy_price_data_df, fromdate=start_date, todate=end_date)  # 加载数据
    rsi_data =  bt.feeds.PandasData(dataname=spy_rsi_data_df, fromdate=start_date, todate=end_date)  
    fear_greed_index_data =  bt.feeds.PandasData(dataname=fear_greed_index_df, fromdate=start_date, todate=end_date)  

    cerebro.adddata(stock_price_data, name='stock_price')  # 将数据传入回测系统
    cerebro.adddata(rsi_data, name="stock_rsi")
    cerebro.adddata(fear_greed_index_data, name='fear_greed_index')
    
    cerebro.addstrategy(MonkeyStrategy)  # 将交易策略加载到回测系统中
    start_cash = 1000000
    cerebro.broker.setcash(start_cash)  # 设置初始资本为 1,000,000
    cerebro.broker.setcommission(commission=0.00012)  # 设置交易手续费为 万分之 1.2
    # cerebro.broker.set_coc(True) # 以订单创建日的收盘价成交 cheat-on-close
    # # cerebro.broker.set_checksubmit(False) # 防止下单时现金不够被拒绝。只在执行时检查现金够不够。
        
    # cerebro.addobserver(ValueTracker)
    # cerebro.addobserver(bt.observers.Value)
    
    cerebro.run()  # 运行回测系统
    
    # assert(broker, bt.brokers.bbroker.BackBroker)
    print(dir(cerebro.broker))
    

    port_value = cerebro.broker.getvalue()  # 获取回测结束后的总资金
    pnl = port_value - start_cash  # 盈亏统计

    print(f"初始资金: {start_cash}\n回测期间: {start_date.strftime('%Y%m%d')} - {end_date.strftime('%Y%m%d')}")
    print(f"总资金: {round(port_value, 2)}")
    print(f"净收益: {round(pnl, 2)}")
    
    start_price = spy_data_df['close'][start_date]
    end_price = spy_data_df['close'][end_date]
    print('市场标普500, 起始日: {:.2f}, 结束日：{:.2f}, 涨幅：{:.2f}%  '.format(start_price, end_price, (end_price/start_price-1)*100))
    
    
    cerebro.plot()

    # # 结合PE
    # # 结合RSI
    # # 结合SAR
    