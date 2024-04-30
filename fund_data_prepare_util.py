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


# def fill_non_trade_day_data(data_df, start_date, end_date) -> pd.DataFrame:
#     ''' 填补非交易日的数据 '''
#     # 如果 start_date 是非交易日, 则用第一个交易日的数据进行填补
#     if data_df['net_value'].get(start_date) == None:
#         first_trade_day_net_value = data_df['net_value'].iloc[0]
#         start_date_df = pd.DataFrame({'date': [start_date], 'net_value': [first_trade_day_net_value]})
#         start_date_df.set_index('date', inplace=True)
#         data_df = pd.concat([start_date_df, data_df])
    
#     # 填补后面的非交易日
#     for i in range((end_date-start_date).days):
#         date = start_date + pd.DateOffset(i+1)        
#         net_value = data_df['net_value'].get(date)
#         if net_value == None:  # 非交易日，用上一个交易日的数据替代
#             last_day_net_value = data_df['net_value'].get(date - pd.DateOffset(1))
#             date_df = pd.DataFrame({'date': [date], 'net_value': [last_day_net_value]})
#             date_df.set_index('date', inplace=True)
#             data_df = pd.concat([data_df, date_df])
    
#     data_df = data_df.sort_index()  
#     return data_df


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
        # fund_data_df = fill_non_trade_day_data(load_fund_data(ticker, start_date, end_date), start_date, end_date)
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
    
    # for item in Portfolio_LaoHuangNiu:
    #     download_fund_data(item[0])
    
    portfolio_df = pd.DataFrame(fund_code.Portfolio_LaoHuangNiu, columns=fund_code.Portfolio_Columns)
    portfolio_df.set_index('ticker', inplace=True)
    
    start_date = pd.to_datetime('2020-04-22')
    end_date = pd.to_datetime('2024-04-22')

    portfolio_funds_data_df = load_portfolio_funds_data(portfolio_df.index, start_date, end_date)
    missing_counts = portfolio_funds_data_df.isnull().sum()
    print(missing_counts)
    
    missing_filled = portfolio_funds_data_df.ffill()
    
    print(missing_filled.isnull().sum())
        
    
