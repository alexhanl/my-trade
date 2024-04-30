import pandas as pd

def calculate_max_dd(value_series: pd.Series):  
    ''' 计算最大回撤 '''
    start_date = value_series.index[0]
    end_date = value_series.index[-1]
    
    dd_peak_date_candidate = dd_peak_date = value_series.index[0]
    dd_bottom_date_candidate = dd_bottom_date = dd_peak_date
    dd_peak_value_candidate = dd_peak_value = value_series.iloc[0]
    dd_bottom_value_candidate = dd_bottom_value = dd_peak_value
    max_dd_candidate = max_dd = dd_peak_value - dd_bottom_value
    
    for i in range((end_date-start_date).days):
        today = start_date + pd.DateOffset(i+1)
        today_value = value_series[today]
        
        if (today_value > dd_peak_value):  # 一个下跌周期计算结束
            
            max_dd = dd_peak_value - dd_bottom_value
            if (max_dd > max_dd_candidate): # 当前的回撤更高
                dd_peak_date_candidate = dd_peak_date
                dd_bottom_date_candidate = dd_bottom_date
                dd_peak_value_candidate = dd_peak_value
                dd_bottom_value_candidate = dd_bottom_value
                max_dd_candidate = max_dd
                
            # 新的可能的下跌周期开始
            dd_peak_date = dd_bottom_date = today
            dd_peak_value = dd_bottom_value = today_value
                    
        elif (today_value < dd_bottom_value):  # 继续下跌
            dd_bottom_date = today
            dd_bottom_value = today_value
    
    # 计算最后一个周期
    max_dd = dd_peak_value - dd_bottom_value      
    if (max_dd > max_dd_candidate): # 当前的回撤更高 查看最后一个
        dd_peak_date_candidate = dd_peak_date
        dd_bottom_date_candidate = dd_bottom_date
        dd_peak_value_candidate = dd_peak_value
        dd_bottom_value_candidate = dd_bottom_value
        max_dd_candidate = max_dd   
    
    return max_dd_candidate, dd_peak_date_candidate, dd_bottom_date_candidate, dd_peak_value_candidate, dd_bottom_value_candidate  
        
