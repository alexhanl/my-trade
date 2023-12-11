# trading


    # for period in periods:
    #     print('---')
    #     for fng_threshold in fng_thresholds:
    #         print(run_strategy(start_date=period[0], end_date=period[1], 
    #                            fear_greed=True, fear_greed_extreme_fear=fng_threshold[0], fear_greed_extreme_greed=fng_threshold[1]))
    #     --- 牛市 ---
    #     (32.71, 99.1)
    #     (40.7, 99.1)
    #     (25.82, 99.1)
    #     --- 熊市 ---
    #     (-8.77, -19.42)
    #     (-14.44, -19.42)
    #     (-8.77, -19.42)
    #     --- 震荡市 ---
    #     (-4.53, 4.25)
    #     (-5.35, 4.25)
    #     (-4.36, 4.25)
    # 只有在熊市，恐贪指数比较有效，并且需要设置较低的情绪值, 但是不能盈利，只是保证比较小的亏损
    
    # for period in periods:
    #     print(run_strategy(start_date=period[0], end_date=period[1], psar=True))
    # (30.33, 99.1)
    # (-4.11, -19.42)
    # (-13.36, 4.25)
    # 只有在熊市，psar比较有效，但是不能盈利，只是保证比较小的亏损
    
    # std_rsi_threshold = (30, 70)
    # aggre_rsi_threshold = (35, 75)
    # conserv_rsi_threshold = (25, 65)
    # rsi_threholds = [std_rsi_threshold, aggre_rsi_threshold, conserv_rsi_threshold]
    
    # for period in periods:
    #     print('---')
    #     for rsi_threhold in rsi_threholds:
    #         print(run_strategy(start_date=period[0], end_date=period[1], 
    #                            rsi=True, rsi_oversold=rsi_threhold[0], rsi_overbought=rsi_threhold[1]))
    # ---牛市---
    # (0.0, 99.1)
    # (7.57, 99.1)
    # (0.0, 99.1)
    # ---熊市---
    # (5.89, -19.42)
    # (-10.39, -19.42)
    # (0.0, -19.42)
    # ---震荡市---
    # (-2.93, 4.25)
    # (-1.24, 4.25)
    # (-13.77, 4.25)
    # 在熊市中，rsi 比较有效， 但是需要采用较为保守的策略。