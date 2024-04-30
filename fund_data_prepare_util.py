import akshare as ak
import pandas as pd
import os

import fund_code 


DATA_PATH='./data'

def download_fund_data(ticker: str):
    """ 
    利用 akshare 下载基金累计净值数据， 并且存放到data/<ticker>.csv文件中 
    """
    data = ak.fund_open_fund_info_em(fund=ticker, indicator="累计净值走势")
    data.columns = ['date', 'net_value']  # 重命名列名，以符合我们的习惯
    filename = ticker + '.csv'
    data.to_csv(os.path.join(DATA_PATH, filename), index=False)
    print("fund ticker {}, downloaded from date {}, to date {}".format(ticker, data.date.min(), data.date.max()))


def load_fund_data(ticker, start_date, end_date) -> pd.DataFrame:
    ''' 
    从 csv 文件中读取加载基金累计净值数据，并且只截取 [start_date, end_date] 区间的数据
    
    Returns:
    pd.DataFrame: index是date, 列包括'net_value'
    '''
    
    data_df = pd.read_csv(os.path.join(DATA_PATH, ticker + '.csv'))
    data_df['date'] = pd.to_datetime(data_df['date'])   
    data_sliced_df = data_df[(data_df['date'] >= start_date) & (data_df['date'] <= end_date)]
    data_sliced_df.set_index('date', inplace=True)
    
    return data_sliced_df


def load_portfolio_funds_data(ticker_series: pd.Series, start_date, end_date) -> pd.DataFrame:
    """
    获取portfolio 中每个基金的累计净值数据。

    Parameters:
    - ticker_series (pd.Series): 基金代码序列。
    - start_date: 开始日期。
    - end_date: 结束日期。

    Returns:
    - DataFrame: 各基金累计净值数据，日期为索引。
                163407  050025  000216  000402
    date        
    2015-01-01  1.3066  1.4547  0.8980  1.0860
    2015-01-02  1.3066  1.4547  0.8980  1.0860
    ...            ...     ...     ...     ...
    2023-10-28  2.1225  3.3480  1.6984  1.5129
    """
    
    # 收集各基金的 DataFrame 列表
    funds_data_frames = []
    for ticker in ticker_series:
        fund_data_df = load_fund_data(ticker, start_date, end_date)  # 暂时不填补非交易日数据，后续再考虑如何填补非交易日数据
        fund_data_df = fund_data_df.rename(columns={'net_value': ticker})
        funds_data_frames.append(fund_data_df)

    # 使用 concat 一次性合并所有 DataFrame
    if funds_data_frames:
        portfolio_funds_data_df = pd.concat(funds_data_frames, axis=1)
    else:
        portfolio_funds_data_df = pd.DataFrame()

    portfolio_funds_data_df = portfolio_funds_data_df.rename_axis('date')
    return portfolio_funds_data_df


if __name__ == "__main__":
    
    for item in fund_code.Portfolio_LaoHuangNiu:
        download_fund_data(item[0])
        
        
    
    # portfolio_df = pd.DataFrame(fund_code.Portfolio_LaoHuangNiu, columns=fund_code.Portfolio_Columns)
    # portfolio_df.set_index('ticker', inplace=True)
    
    # start_date = pd.to_datetime('2020-04-22')
    # end_date = pd.to_datetime('2024-04-22')

    # portfolio_funds_data_df = load_portfolio_funds_data(portfolio_df.index, start_date, end_date)
    # missing_counts = portfolio_funds_data_df.isnull().sum()
    # print(missing_counts)
    
    # missing_filled = portfolio_funds_data_df.ffill()
    
    # print(missing_filled.isnull().sum())
        
    
