from IPython.display import display
import numpy as np
import sqlite3 as sl
import pandas as pd
import datetime
import numpy as np
import pickle
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def plot_coins(coin, HYPE, CLOSE):
    plt.figure(coin)
    plt.plot(CLOSE, color="green")
    plt.xlabel("Date & Time")
    plt.ylabel("Value $")
    plt2=plt.twinx()
    plt2.plot(HYPE)
    plt2.plot(HYPE.diff(periods=1))
    plt2.plot(HYPE.diff(periods=10))
    #plt2.plot(HYPE.diff(periods=2))
    plt2.set_ylabel("Hype %")
    plt2.legend(['Close price'])
    plt.legend(['Buy Indicator', 'differential 1', 'differential 10'])
    plt.title(coin)
    plt.show(block=False)


con = sl.connect("crypto_database.db")
cur = con.cursor()

artifact_id = 188

closeString = 'SELECT date, close FROM artifact_price WHERE artifact_id="{}"'.format(artifact_id)
hypeString = 'SELECT date, hype FROM artifact_trend WHERE artifact_id="{}"'.format(artifact_id)

value = pd.read_sql_query(closeString, con)
trend = pd.read_sql_query(hypeString, con)
con.close()
#value = value.set_index('date')
#trend = trend.set_index('date')
value['date']= pd.to_datetime(value['date'])
trend['date']= pd.to_datetime(trend['date'])
#print(value.info())
#print(trend.info())
#trade = pd.read_pickle("./trade_data_05_12_first.pkl")
#ax.plot(value, color="red")
plt.plot(trend['date'], trend['hype'],  color="blue")

plt.xticks(rotation=90)
#ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(ax.xaxis.get_major_locator()))

plt2=plt.twinx()
plt2.plot(value['date'], value['close'],  color="red")

#plt.grid()
#plot_coins(artifact_id, trend, value)
plt.show()
