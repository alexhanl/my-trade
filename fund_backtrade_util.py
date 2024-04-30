import pandas as pd

def fund_portfolio_back_trade(portfolio_df, start_date, end_date, rebalance_period, portfolio_funds_data_df):
    TOTAL_INVESTMENT = 100.0
    funds_value_dict = {}  # map of fund ticker to fund_value_df  对应与excel中，每个fund一个sheet，每个sheet记录 date，net_value（当天的基金单位净值），shares（持有份额），fund_value（基金持仓价值）
    portfolio_value_series = pd.Series()  # portfolio_total_value_series 记录每天的portfolio的价值

    # calculate the initial number of shares, fund value and total fund value
    start_date_net_value_series = portfolio_funds_data_df.iloc[0]
    # print(start_date_net_value_series)
    for ticker, target_percent in portfolio_df['target_percent'].items():
        start_date_net_value = start_date_net_value_series[ticker]
        fund_value = TOTAL_INVESTMENT * target_percent / 100 
        shares = fund_value / start_date_net_value
        funds_value_dict[ticker] = pd.DataFrame([[start_date, start_date_net_value, shares, fund_value]], 
                                               columns=['date', 'net_value', 'shares', 'fund_value'])

    # 计算start_date的初始 portfolio 整体 value，在没有佣金的情况下，应该为 TOTAL_INVESTMENT，也就是100
    current_portfolio_value = sum(funds_value_dict[ticker]['fund_value'].iloc[0] for ticker in portfolio_df.index)

    portfolio_value_series[start_date] = current_portfolio_value

    # 计算每天的基金价值变化，从第二天开始
    day_counter = 0
    for date, funds_net_value in portfolio_funds_data_df.iloc[1:].iterrows():
        day_counter = day_counter + 1
        current_portfolio_value = 0.0
        for ticker in portfolio_df.index:
            net_value = funds_net_value[ticker]
            shares = funds_value_dict[ticker]['shares'].iloc[-1]  # 在没有交易的情况下，基金份额保持不变，直接获取上一日的数据即可
            fund_value = net_value * shares
            funds_value_dict[ticker] = pd.concat([funds_value_dict[ticker], 
                                                 pd.DataFrame([[date, net_value, shares, fund_value]], 
                                                              columns = ['date', 'net_value', 'shares', 'fund_value'])], 
                                                axis=0, ignore_index=True)
            current_portfolio_value = current_portfolio_value + fund_value

        portfolio_value_series[date] = current_portfolio_value
        
        # 重平衡，为了计算简单，直接在盘后即进行变更，并修正最后一行的数据（即当天的数据）
        if day_counter % rebalance_period == 0: 
            # print("---- 阶段业绩：  {} - {} ----".format( (date - pd.Timedelta(days=rebalance_period)).date(), date.date()))
            for ticker in portfolio_df.index:
                fund_value_df = funds_value_dict[ticker]
                target_percent = portfolio_df.loc[ticker, 'target_percent']
                fund_value_change = current_portfolio_value * target_percent/100 - fund_value_df['fund_value'].iloc[-1]  # 正数表示未达到target_percent，需要加仓。负数相反
                
                # fund_name = portfolio_df.loc[ticker, 'name']
                # profit = fund_value_df['fund_value'].iloc[-1] - fund_value_df['fund_value'].iloc[-rebalance_period]
                # print("{} 利润比例为 {:.2f} %".format(fund_name, profit/fund_value_df['fund_value'].iloc[-rebalance_period] * 100))
                
                shares_change =  fund_value_change / fund_value_df['net_value'].iloc[-1]  # 正数表示需要增加份额
                fund_value_df.loc[fund_value_df.index[-1], 'shares'] += shares_change
                fund_value_df.loc[fund_value_df.index[-1], 'fund_value'] = current_portfolio_value * target_percent/100
    
    return portfolio_value_series
