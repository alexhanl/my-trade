import akshare as ak
import pandas as pd

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




