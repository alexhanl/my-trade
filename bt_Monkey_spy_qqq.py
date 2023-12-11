import backtrader as bt
import matplotlib.pyplot as plt
import akshare as ak
import pandas as pd
import os

from datetime import datetime, timedelta
from common import Signal, Loglevel
from common import MyParabolicSAR, MyDrawDown
from common import RsiFngPandasData, RsiFngObserver
from common import ProfitLossAnalyzer, ValueRecorder

DATA_PATH='./data'

psar_s = pd.Series()  

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
        ('loglevel', Loglevel.SUMMARY)
    )

    def log(self, txt, dt=None):
        if self.p.loglevel == Loglevel.DETAIL:
            ''' Logging function fot this strategy'''
            dt = dt or self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))        
        
    def __init__(self):
        self.close_price = self.datas[0].close  # 指定价格序列
        self.fear_greed = self.datas[0].fear_greed    
        self.psar = MyParabolicSAR(period=20, af = 0.015)
        self.rsi = bt.indicators.RSI_Safe(self.data.close, period=14)
        # self.rsi = self.datas[0].rsi
        self.sma = bt.indicators.SimpleMovingAverage(self.data.close, period=50)
        
        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None
        
        # 用来记录出现buy或者sell信号的次数
        self.psar_buy_signal_counter = 0
        self.psar_sell_signal_counter = 0
        
        self.first_day = True
        
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
        # 注释掉的代码是为了可以避开某些特殊时间
        # dt = self.datas[0].datetime.date(0)
        
        # if (dt.isoformat() > datetime(2021,11,26).isoformat()) & (dt.isoformat() < datetime(2021,12,13).isoformat()):
        #     return NO_SIGNAL
        
        if self.fear_greed[0] < self.p.fear_greed_extreme_fear:
            return Signal.BUY_SIGNAL
        elif self.fear_greed[0] > self.p.fear_greed_extreme_greed:
            return Signal.SELL_SIGNAL    
        return Signal.NO_SIGNAL
    
    def check_psar_indicator(self):
        if self.psar[0] < self.close_price[0]:
            self.psar_sell_signal_counter = 0
            if self.psar_buy_signal_counter == self.p.psar_sensitivity - 1:
                self.psar_buy_signal_counter = 0
                return Signal.BUY_SIGNAL
            else:
                self.psar_buy_signal_counter = self.psar_buy_signal_counter + 1
        elif self.psar[0] > self.close_price[0]:
            self.psar_buy_signal_counter = 0
            if self.psar_sell_signal_counter == self.p.psar_sensitivity - 1:
                self.psar_sell_signal_counter = 0
                return Signal.SELL_SIGNAL
            else:
                self.psar_sell_signal_counter = self.psar_sell_signal_counter + 1   
        return Signal.NO_SIGNAL

    def check_rsi_indicator(self):
        if self.rsi[0] < self.p.rsi_oversold:
            return Signal.BUY_SIGNAL
        elif self.rsi[0] > self.p.rsi_overbought:
            return Signal.SELL_SIGNAL
        return Signal.NO_SIGNAL

    def check_indicators(self):         
        signals = []
        
        if self.p.fear_greed:
            signals.append(self.check_fear_greed_indicator())
        if self.p.rsi:
            signals.append(self.check_rsi_indicator())
        if self.p.psar:
            signals.append(self.check_psar_indicator())
        
        num_of_buy = signals.count(Signal.BUY_SIGNAL)
        if num_of_buy / len(signals) > 0.5:  # 如果大部分indicator提示买入
            return Signal.BUY_SIGNAL
        
        num_of_sell = signals.count(Signal.SELL_SIGNAL)
        if num_of_sell / len(signals) > 0.5:
            return Signal.SELL_SIGNAL
             
        return Signal.NO_SIGNAL
    
    # 用来记录psar并且存入文件   
    def record_psar(self):
        psar = self.psar[0]
        date = self.datas[0].datetime.date(0)
        psar_s[date] = psar
    
    def all_in(self):
        size = int(self.broker.get_cash() / self.close_price[0])
        if size > 0:
            self.log('Indicators for BUY: RSI: %.2f, Fear_Greed: %.2f' % (self.rsi[0], self.fear_greed[0]))
            self.log('BUY CREATE, Price = %.2f, Shares = %.2f' % (self.close_price[0], size))
            self.order = self.buy(size=size)
    
    def close_position(self):
        self.log('Indicators for SELL: RSI: %.2f, Fear_Greed: %.2f' % (self.rsi[0], self.fear_greed[0]))
        self.log('SELL CREATE, Price = %.2f, Shares = %.2f' % (self.close_price[0], self.position.size))
        self.order = self.sell(size=self.position.size)
    
    
    
    def next(self):
        # self.record_psar()
        # return
        
        if self.order:  # 检查是否有指令等待执行,
            return
        
        if self.first_day:
            self.all_in()
            self.first_day = False
        
        # signal = self.check_indicators()
        
        # if signal == Signal.BUY_SIGNAL:            
        #     self.all_in()
        # elif signal == Signal.SELL_SIGNAL and self.position.size > 0:
        #     self.close_position()


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
                 psar_sensitivity: int = 1,
                 plotting: bool = False,
                 loglevel: int = Loglevel.SUMMARY):
    
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
    
    data = RsiFngPandasData(dataname=data_df, fromdate=start_date, todate=end_date, rsi=6, fear_greed=7)
    cerebro.adddata(data)
    
    cerebro.addstrategy(MonkeyStrategy, 
                        fear_greed = fear_greed,
                        fear_greed_extreme_fear = fear_greed_extreme_fear,
                        fear_greed_extreme_greed = fear_greed_extreme_greed,
                        rsi = rsi,                                              
                        rsi_oversold = rsi_oversold,
                        rsi_overbought = rsi_overbought,
                        psar = psar,
                        psar_sensitivity = psar_sensitivity,
                        loglevel = loglevel)  # 将交易策略加载到回测系统中
    start_cash = 1000000
    cerebro.broker.setcash(start_cash)  # 设置初始资本为 1,000,000
    # cerebro.broker.setcommission(commission=0.00012)  # 设置交易手续费为 万分之 1.2
    cerebro.broker.set_coc(True) # 以订单创建日的收盘价成交 cheat-on-close, 为了避免第二天开盘价格上涨，导致买入失败
            
    cerebro.addobserver(bt.observers.Value)
    cerebro.addobserver(bt.observers.BuySell)
    cerebro.addobserver(RsiFngObserver)
    # cerebro.addanalyzer(ProfitLossAnalyzer, _name='profit_loss')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(MyDrawDown, _name='mydrawdown')  
    cerebro.addanalyzer(ValueRecorder, _name='value_recorder')
    
    
    results = cerebro.run(stdstats=False)  # 运行回测系统
    
    strat = results[0]    
    port_value = cerebro.broker.getvalue()  # 获取回测结束后的总资金
    pnl = port_value - start_cash  # 盈亏统计

    if loglevel >= Loglevel.SUMMARY:
        print(f"初始资金: {start_cash}\n回测期间: {start_date.strftime('%Y%m%d')} - {end_date.strftime('%Y%m%d')}")
        print(f"总资金: {round(port_value, 2)}")
        print(f"净收益: {round(pnl, 2)}")
        # results[0].analyzers.profit_loss.print_result()
        # print('最大回撤: %.2f' % strat.analyzers.drawdown.get_analysis()['max']['drawdown'])
        
        mdd = strat.analyzers.mydrawdown.get_analysis()
        print('最大回撤：{:.2f}%, 开始日期 {}, 结束日期 {}'.format(mdd['max_drawdown']*100, mdd['max_drawdown_start'], mdd['max_drawdown_end']))
       
    
    start_price = data_df['close'].iloc[0]
    end_price = data_df['close'].iloc[-1]
    
    if loglevel >= Loglevel.SUMMARY:
        print('{}, 起始日: {:.2f}, 结束日：{:.2f}, 涨幅：{:.2f}%  '.format(ticker, start_price, end_price, (end_price/start_price-1)*100))
    
    if plotting:
        cerebro.plot()
    
    # return round(pnl/10000, 2), round((end_price/start_price-1)*start_cash/10000, 2)

def run_backtrade():
    spy_bull_period = (datetime(2020,3,16), datetime(2022,1,4))
    spy_bear_period = (datetime(2022,1,3), datetime(2022,10,25))
    spy_volatile_period = (datetime(2006,1,31), datetime(2012,6,12))
    spy_periods = [spy_bull_period, spy_bear_period, spy_volatile_period]
    
    spy_full_period = (datetime(2003,12,11), datetime(2023,11,24))
    
    last_5_years = (spy_full_period[1] - timedelta(days=5*365), spy_full_period[1])
    
    std_fng_threshold = (25, 75)
    aggressive_fng_threshold = (30, 80)
    conserv_fng_threshold = (20, 70)
    fng_thresholds = [std_fng_threshold, aggressive_fng_threshold, conserv_fng_threshold]
    
    run_strategy(ticker='spy', start_date=last_5_years[0], end_date=last_5_years[1], psar=True, loglevel=Loglevel.DETAIL, plotting=True)
    
    pass
    
if __name__ == '__main__':
    run_backtrade()
    
    # psar_s.to_csv('data/qqq_psar.csv')
