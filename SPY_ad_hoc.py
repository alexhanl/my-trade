from datetime import datetime, timedelta
import matplotlib.ticker as ticker
import backtrader as bt

import matplotlib.pyplot as plt
import akshare as ak
import pandas as pd

import os

plt.rcParams["font.sans-serif"] = ["SimHei"]  # 设置字体
plt.rcParams["axes.unicode_minus"] = False    # 该语句解决图像中的“-”负号的乱码问题



DATA_PATH = './data'

today = datetime.now().date()   #.strftime('%Y-%m-%d')
ten_years_ago = today - timedelta(days=10*365)
five_years_ago = today - timedelta(days=5*365)
three_yeas_ago = today - timedelta(days=3*365)
one_year_ago = today - timedelta(days=365)

last_date = datetime(2023,11,24)


start_date = datetime(2016,1,1)
end_date = today


data_df = pd.read_csv(os.path.join(DATA_PATH, 'spy.csv'))
data_df['date'] = pd.to_datetime(data_df['date'], format='%Y-%m-%d') 
data_df.set_index('date', inplace=True)
    
fear_greed_index_df = pd.read_csv(os.path.join(DATA_PATH, 'all_fng_csv.csv'))
fear_greed_index_df.rename(columns={'Date': 'date'}, inplace=True)
fear_greed_index_df['date'] = pd.to_datetime(fear_greed_index_df['date'], format='%Y-%m-%d') 
fear_greed_index_df.set_index('date', inplace=True)
    
data_df['fear_greed'] = fear_greed_index_df['Fear Greed']    

data_df = data_df[(data_df.index >= pd.to_datetime(start_date)) & (data_df.index <= pd.to_datetime(end_date))]

x = data_df.index
y1 = data_df['close']
y2 = data_df['fear_greed']


fig, ax1 = plt.subplots()
ax1.plot(x, y1, 'b-')
ax1.set_xlabel('date')
ax1.set_ylabel('index', color='b')
for tl in ax1.get_yticklabels():
    tl.set_color('b')
ax1.grid(True, axis='x') 
ax1.yaxis.set_major_locator(ticker.MultipleLocator(10))
    
ax2 = ax1.twinx()
ax2.plot(x, y2, 'r-')
ax2.set_ylabel('fear_greed', color='r')
for tl in ax2.get_yticklabels():
    tl.set_color('r')

ax2.axhline(y=25, color='grey', linestyle='dashed')
ax2.axhline(y=75, color='grey', linestyle='dashed')
ax2.yaxis.set_major_locator(ticker.MultipleLocator(5))

plt.title('SPY')

plt.show()


if __name__ == '__main__':
    pass