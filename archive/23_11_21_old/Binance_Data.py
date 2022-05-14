import pandas as pd
import time
import websocket
import json, pprint, talib 
import numpy
from binance.client import Client
from binance.enums import *

api_key = 'ihvXWbHvvDrYuroIJOS9ANW6X7tv5OQSYibLLloKyIGui0w93Q5yUJOBZclnNL5D'
api_secret = 'uzmKBJ3lmVS4TsTl2AOHVJOYTFfLM5qrg00vAqUyTYbSjiy7BDPlTpaq2Oy7qdo2'

client = Client(api_key, api_secret)

def get_all_tokens():
    #filter out leverage tokens, non usd tokens, 
    all_pairs = pd.DataFrame(client.get_ticker())
    relev = all_pairs[all_pairs.symbol.str.contains('USDT')]
    non_lev_list = relev[ ~( (relev.symbol.str.contains('UP')) | (relev.symbol.str.contains('DOWN')) ) ]
    sorted = non_lev_list.sort_values(by='priceChangePercent', ascending=False)
    return sorted

#format (symbol, interval, 120 mins ago, now) or (symbol, interval, start date, end date) "1 Dec, 2017"
def getminutedata(symbol, interval, start, end):
    if(end == 'now'):
        frame = pd.DataFrame(client.get_historical_klines(symbol,
                                                        interval,
                                                        start + ' min ago UTC'))
    else:
        frame = pd.DataFrame(client.get_historical_klines(symbol, 
                                                        interval, 
                                                        start, 
                                                        end))
    frame = frame.iloc[:,:6]                                                    
    frame.columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume']
    frame = frame.set_index('Time')
    frame.index = pd.to_datetime(frame.index, unit= 'ms')
    frame = frame.astype(float)
    return frame
#print(get_all_tokens())


#mobox = getminutedata('MOBOX', '1m', "9 Nov, 2021", "14 Nov, 2021")
time = str(60*24*5)
mobox = getminutedata('TOMOUSDT', '1m', time, 'now')['Close']
print(mobox)
