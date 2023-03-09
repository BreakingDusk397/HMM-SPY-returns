import yfinance as yf
import pandas as pd
import datetime 
tod = datetime.datetime.now()
d = datetime.timedelta(days = 60)
a = tod - d
print(a.strftime('%Y-%m-%d'))

dates = []
for i in list(range(1,12,1)):
    d = datetime.timedelta(days = (60 * i))
    a = tod - d
    a = a.strftime('%Y-%m-%d')
    dates.append(str(a))

print('dates: \n',dates)

end_dates = []
for i in list(range(1,12,1)):
    d = datetime.timedelta(days = (61 * i))
    a = tod - d
    a = a.strftime('%Y-%m-%d')
    end_dates.append(str(a))
end_dates = [tod.strftime('%Y-%m-%d')] + end_dates
end_dates.pop()
print('dates: \n',end_dates)

#data = yf.download("SPY", start="2017-01-01", end=tod.strftime('%Y-%m-%d'))

total_df = []
for x,y in zip(dates,end_dates):
    data = yf.download(tickers = "SPY",  # list of tickers
                start=str(x), 
                end=str(y),        
                interval = "1m",       # trading interval
                ignore_tz = True,      # ignore timezone when aligning data from different exchanges?
                prepost = False)       # download pre/post market hours data?
    total_df.insert(0,data)


total_df = pd.concat(total_df, axis=0)
total_df['date'] = total_df.index
total_df['date'] = pd.to_datetime(total_df.date, utc=False)
total_df.sort_values(by='date',ascending=False)



#total_df.index = total_df.index.tz_convert('America/New_York')
#print(total_df)
#total_df = pd.concat([total_df,df],axis=1)
print(total_df)


total_df.to_csv('hourly_yf_SPY_OHLCV2.csv')
