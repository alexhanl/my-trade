import akshare as ak
import pandas as pd
from enum import IntEnum
import backtrader as bt

def prepare_cn_fund_data(fundcode):
    fund_data_df = ak.fund_open_fund_info_em(fund=fundcode, indicator="累计净值走势")
    fund_data_df.columns = [
        'date',
        'close'
    ]
    fund_data_df.index = pd.to_datetime(fund_data_df['date'])
    fund_data_df['open'] = fund_data_df['close'].copy(deep=True)
    fund_data_df['high'] = fund_data_df['close'].copy(deep=True)
    fund_data_df['low'] = fund_data_df['close'].copy(deep=True)
    fund_data_df['volume'] = 0

    return fund_data_df

class Signal(IntEnum):
    SELL_SIGNAL = -1
    BUY_SIGNAL = 1
    NO_SIGNAL = 0

class Loglevel(IntEnum):
    SUMMARY = 1
    DETAIL = 2


class MyParabolicSAR(bt.indicators.ParabolicSAR):
    plotlines = dict(
        psar=dict(color='green', markersize='1')  # 将PSAR指标的颜色设置为红色
    )

class MyDrawDown(bt.Analyzer):
    def __init__(self):
        self.drawdown = 0.0
        self.max_drawdown = 0.0
        self.drawdown_start = None
        self.max_drawdown_start = None
        self.max_drawdown_end = None
        self.peak = None

    def next(self):
        current_value = self.strategy.broker.get_value()
        self.peak = max(self.peak, current_value) if self.peak is not None else current_value

        self.drawdown = (self.peak - current_value) / self.peak
        if self.drawdown > self.max_drawdown:
            self.max_drawdown = self.drawdown
            self.max_drawdown_start = self.drawdown_start
            self.max_drawdown_end = self.data.datetime.date()

        if self.drawdown == 0:
            self.drawdown_start = self.data.datetime.date()

    def get_analysis(self):
        return dict(max_drawdown=self.max_drawdown,
                    max_drawdown_start=self.max_drawdown_start,
                    max_drawdown_end=self.max_drawdown_end)


class RsiFngPandasData(bt.feeds.PandasData):
    lines = ('rsi', 'fear_greed')
    params = (('rsi', -1), ('fear_greed', -1))
    plotinfo = {"plot": True, "subplot": True}
    
class RsiFngObserver(bt.Observer):
    lines = ('rsi', 'fear_greed',)
    plotinfo = dict(plot=True, subplot=True)
    def next(self):
        self.lines.rsi[0] = self.datas[0].rsi[0]
        self.lines.fear_greed[0] = self.datas[0].fear_greed[0]
        
        
class ProfitLossAnalyzer(bt.Analyzer):
    def __init__(self):
        self.trades = []

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.buyprice = order.executed.price
            elif order.issell():
                sellprice = order.executed.price
                profit = sellprice - self.buyprice
                self.trades.append(profit)

    def print_result(self):
        positive_profit_list = [i for i in self.trades if i >= 0]    
        negative_profit_list = [i for i in self.trades if i < 0] 
        print('一共交易 {} 次，其中 {} 次为盈利，{} 次为亏损'.format(len(self.trades), len(positive_profit_list), len(negative_profit_list)))


class ValueRecorder(bt.Analyzer):
    def __init__(self):
        self.values = {}

    def next(self):
        date = self.data.datetime.date()
        value = self.strategy.broker.getvalue()
        self.values[date] = value

    def get_analysis(self):
        return self.values