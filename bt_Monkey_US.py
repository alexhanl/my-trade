from datetime import datetime

import backtrader as bt

import matplotlib.pyplot as plt
import akshare as ak
import pandas as pd

import os

SELL_SIGNAL = -1
BUY_SIGNAL = 1
NO_SIGNAL = 0

class MonkeyStrategy(bt.Strategy):

    params = (
        ('fear_greed', False),
        ('fear_greed_extreme_fear', 25),
        ('fear_greed_extreme_greed', 75),
        ('rsi', False),
        ('rsi_oversold', 30),
        ('rsi_overbought', 70),
        ('psar', False),
        ('psar_sensitivity', 1),
        ('printout', False)
    )
    

    def log(self, txt, dt=None):
        if self.p.printout:
            ''' Logging function fot this strategy'''
            dt = dt or self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))
            
        
    def __init__(self):
        self.close_price = self.datas[0].close  # 指定价格序列
        self.fear_greed = self.datas[0].fear_greed        
        
        self.psar = bt.indicators.ParabolicSAR(period=20, af = 0.015)
        self.rsi = bt.indicators.RSI_Safe(self.data.close, period=14)
        
        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None
        
        self.psar_buy_signal_counter = 0
        self.psar_sell_signal_counter = 0
        
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

    def check_fear_greed_indicator(self):
        if self.fear_greed[0] < self.p.fear_greed_extreme_fear:
            return BUY_SIGNAL
        elif self.fear_greed[0] > self.p.fear_greed_extreme_greed:
            return SELL_SIGNAL    
        return NO_SIGNAL
    
    def check_psar_indicator(self):
        if self.psar[0] < self.close_price[0]:
            self.psar_sell_signal_counter = 0
            if self.psar_buy_signal_counter == self.p.psar_sensitivity - 1:
                self.psar_buy_signal_counter = 0
                return BUY_SIGNAL
            else:
                self.psar_buy_signal_counter = self.psar_buy_signal_counter + 1
        elif self.psar[0] > self.close_price[0]:
            self.psar_buy_signal_counter = 0
            if self.psar_sell_signal_counter == self.p.psar_sensitivity - 1:
                self.psar_sell_signal_counter = 0
                return SELL_SIGNAL
            else:
                self.psar_sell_signal_counter = self.psar_sell_signal_counter + 1   
        return NO_SIGNAL

    def check_rsi_indicator(self):
        if self.rsi[0] < self.p.rsi_oversold:
            return BUY_SIGNAL
        elif self.rsi[0] > self.p.rsi_overbought:
            return SELL_SIGNAL
        return NO_SIGNAL

    def check_indicators(self): 
        
        if self.p.fear_greed:
            return self.check_fear_greed_indicator()
        
        if self.p.rsi:
            return self.check_rsi_indicator()
        
        if self.p.psar:
            return self.check_psar_indicator()
        
        return NO_SIGNAL
        
       
    
    def next(self):
        if self.order:  # 检查是否有指令等待执行,
            return
        
        # self.log('Close: {:.2f}, RSI:  {:.2f}, Fear_Greed: {:.2f}'.format(self.close_price[0], self.rsi[0], self.fear_greed[0]))
        
        signal = self.check_indicators()
        
        if signal == 1:            
            size = int(self.broker.get_cash() / self.close_price[0])
            if size > 0:
                self.log('Indicators for BUY: RSI: %.2f, Fear_Greed: %.2f' % (self.rsi[0], self.fear_greed[0]))
                self.log('BUY CREATE, Price = %.2f, Shares = %.2f' % (self.close_price[0], size))
                self.order = self.buy(size=size)
        elif signal == -1 and self.position.size > 0:
            self.log('Indicators for SELL: RSI: %.2f, Fear_Greed: %.2f' % (self.rsi[0], self.fear_greed[0]))
            self.log('SELL CREATE, Price = %.2f, Shares = %.2f' % (self.close_price[0], self.position.size))
            self.order = self.sell(size=self.position.size)

    
DATA_PATH='./data'

class CustomPandasData(bt.feeds.PandasData):
    lines = ('rsi', 'fear_greed')
    params = (('rsi', -1), ('fear_greed', -1))
    plotinfo = {"plot": True, "subplot": True}

class CustomObserver(bt.Observer):
    lines = ('rsi', 'fear_greed',)

    plotinfo = dict(plot=True, subplot=True)

    def next(self):
        self.lines.rsi[0] = self.datas[0].rsi[0]
        self.lines.fear_greed[0] = self.datas[0].fear_greed[0]

def run_strategy(ticker: str = 'spy', 
                 start_date: datetime = datetime(2023, 1, 1), 
                 end_date: datetime = datetime(2023, 12, 31), 
                 fear_greed: bool = False,
                 fear_greed_extreme_fear: int = 25,
                 fear_greed_extreme_greed: int = 75,
                 rsi: bool = False,
                 rsi_oversold: int = 30, 
                 rsi_overbought: int = 70,
                 psar: bool = False,
                 psar_sensitivity: int = 1):
    data_df = pd.read_csv(os.path.join(DATA_PATH, ticker + '.csv'))
    data_df['date'] = pd.to_datetime(data_df['date'], format='%Y-%m-%d') 
    data_df.set_index('date', inplace=True)
    
    fear_greed_index_df = pd.read_csv(os.path.join(DATA_PATH, 'all_fng_csv.csv'))
    fear_greed_index_df.rename(columns={'Date': 'date'}, inplace=True)
    fear_greed_index_df['date'] = pd.to_datetime(fear_greed_index_df['date'], format='%Y-%m-%d') 
    fear_greed_index_df.set_index('date', inplace=True)
    
    data_df['fear_greed'] = fear_greed_index_df['Fear Greed']    
    
    cerebro = bt.Cerebro()  # 初始化回测系统
    
    data_df = data_df[(data_df.index >= start_date) & (data_df.index <= end_date)]
    
    data = CustomPandasData(dataname=data_df, fromdate=start_date, todate=end_date, rsi=6, fear_greed=7)
    # data = CustomPandasData(dataname=data_df, rsi=6, fear_greed=7)
    cerebro.adddata(data)
    
    cerebro.addstrategy(MonkeyStrategy, 
                        fear_greed = fear_greed,
                        fear_greed_extreme_fear = fear_greed_extreme_fear,
                        fear_greed_extreme_greed = fear_greed_extreme_greed,
                        rsi = rsi,                                              
                        rsi_oversold = rsi_oversold,
                        rsi_overbought = rsi_overbought,
                        psar = psar,
                        psar_sensitivity = psar_sensitivity)  # 将交易策略加载到回测系统中
    start_cash = 1000000
    cerebro.broker.setcash(start_cash)  # 设置初始资本为 1,000,000
    # cerebro.broker.setcommission(commission=0.00012)  # 设置交易手续费为 万分之 1.2
    cerebro.broker.set_coc(True) # 以订单创建日的收盘价成交 cheat-on-close
            
    cerebro.addobserver(bt.observers.Value)
    cerebro.addobserver(bt.observers.BuySell)
    cerebro.addobserver(CustomObserver)
    
    cerebro.run(stdstats=False)  # 运行回测系统

    port_value = cerebro.broker.getvalue()  # 获取回测结束后的总资金
    pnl = port_value - start_cash  # 盈亏统计

    
    # print(f"初始资金: {start_cash}\n回测期间: {start_date.strftime('%Y%m%d')} - {end_date.strftime('%Y%m%d')}")
    # print(f"总资金: {round(port_value, 2)}")
    # print(f"净收益: {round(pnl, 2)}")
    
    start_price = data_df['close'].iloc[0]
    end_price = data_df['close'].iloc[-1]
    # print('市场标普500, 起始日: {:.2f}, 结束日：{:.2f}, 涨幅：{:.2f}%  '.format(start_price, end_price, (end_price/start_price-1)*100))
    
    return round(pnl/10000, 2), round((end_price/start_price-1)*start_cash/10000, 2)
    # cerebro.plot()


def backtrade_single_signal():
    bull_period = (datetime(2020,3,16), datetime(2022,1,4))
    bear_period = (datetime(2022,1,3), datetime(2022,10,25))
    volatile_period = (datetime(2006,1,31), datetime(2012,6,12))
    periods = [bull_period, bear_period, volatile_period]
    
    
    std_fng_threshold = (25, 75)
    aggre_fng_threshold = (30, 80)
    conserv_fng_threshold = (20, 70)
    fng_thresholds = [std_fng_threshold, aggre_fng_threshold, conserv_fng_threshold]
    
    # for period in periods:
    #     print('---')
    #     for fng_threshold in fng_thresholds:
    #         print(run_strategy(start_date=period[0], end_date=period[1], 
    #                            fear_greed=True, fear_greed_extreme_fear=fng_threshold[0], fear_greed_extreme_greed=fng_threshold[1]))
    # 只有在熊市，恐贪指数比较有效，并且需要设置较低的情绪值, 但是不能盈利，只是保证比较小的亏损
    
    for period in periods:
        print(run_strategy(start_date=period[0], end_date=period[1], psar=True))
    # 只有在熊市，psar比较有效，但是不能盈利，只是保证比较小的亏损
    
    std_rsi_threshold = (30, 70)
    aggre_rsi_threshold = (35, 75)
    conserv_rsi_threshold = (25, 65)
    rsi_threholds = [std_rsi_threshold, aggre_rsi_threshold, conserv_rsi_threshold]
    
    # for period in periods:
    #     print('---')
    #     for rsi_threhold in rsi_threholds:
    #         print(run_strategy(start_date=period[0], end_date=period[1], 
    #                            rsi=True, rsi_oversold=rsi_threhold[0], rsi_overbought=rsi_threhold[1]))
    # 在熊市中，rsi 比较有效， 但是需要采用较为保守的策略。


if __name__ == '__main__':
    
    # run_strategy(ticker='spy', 
    #              start_date=datetime(2020, 1, 16), 
    #              end_date=datetime(2023, 11, 24)
    #              )
    
    backtrade_single_signal()
    

        