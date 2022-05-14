import pandas as pd
import time
import websocket
import json, pprint, talib 
import numpy
import csv

from binance.client import Client
from binance.enums import *
from coinmarketcapapi import CoinMarketCapAPI, CoinMarketCapAPIError

from pytrends.request import TrendReq
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.dates as mdates

cmc = CoinMarketCapAPI('a01ace6b-f43c-439e-9fca-dc7f73e2a648')
api_key = 'ihvXWbHvvDrYuroIJOS9ANW6X7tv5OQSYibLLloKyIGui0w93Q5yUJOBZclnNL5D'
api_secret = 'uzmKBJ3lmVS4TsTl2AOHVJOYTFfLM5qrg00vAqUyTYbSjiy7BDPlTpaq2Oy7qdo2'
client = Client(api_key, api_secret)

def get_all_tokens():
    #filter out leverage tokens, non usd tokens, 
    all_pairs = pd.DataFrame(client.get_ticker())
    relev = all_pairs[all_pairs.symbol.str.endswith('USDT')]
    non_lev_list = relev[ ~( (relev.symbol.str.contains('UP')) | (relev.symbol.str.contains('DOWN')) | (relev.symbol.str.contains('BEAR')) | (relev.symbol.str.contains('BULL')) ) ]
    #filter out stable coins
    non_stable_rm = non_lev_list[~all_pairs.symbol.str.startswith('USD')]
    #remove BCHSV, PAX, STRAT, XZC
    non_stable_rm = non_stable_rm.drop( non_stable_rm[non_stable_rm.symbol == 'BCHSVUSDT'].index )
    non_stable_rm = non_stable_rm.drop( non_stable_rm[non_stable_rm.symbol == 'PAXUSDT'].index ) # dollar value
    non_stable_rm = non_stable_rm.drop( non_stable_rm[non_stable_rm.symbol == 'STRATUSDT'].index )
    non_stable_rm = non_stable_rm.drop( non_stable_rm[non_stable_rm.symbol == 'XZCUSDT'].index )
    non_stable_rm = non_stable_rm.drop( non_stable_rm[non_stable_rm.symbol == 'AUDUSDT'].index ) # non crypto
    non_stable_rm = non_stable_rm.drop( non_stable_rm[non_stable_rm.symbol == 'EURUSDT'].index ) # non crypto
    non_stable_rm = non_stable_rm.drop( non_stable_rm[non_stable_rm.symbol == 'GBPUSDT'].index ) # non crypto
    non_stable_rm = non_stable_rm.drop( non_stable_rm[non_stable_rm.symbol == 'BCCUSDT'].index ) # BitConnect scam
    non_stable_rm = non_stable_rm.drop( non_stable_rm[non_stable_rm.symbol == 'BCHABCUSDT'].index ) # Bitcoin Cash ABC (BCHA) Rebrand to eCash (XEC)
    
    #sorted = non_stable_rm.sort_values(by='priceChangePercent', ascending=False)
    sorted = non_stable_rm.sort_values(by='symbol', key=lambda x: x.str.split('USDT').str[0])

    token_tickers = sorted
    symbols=token_tickers['symbol'].str.slice(0,-4)
    symbols = symbols.replace('GXS', 'GXC')
    symbols = symbols.replace('IOTA', 'MIOTA')
    symbolslist = ",".join(symbols)

    cmcinfo = cmc.cryptocurrency_info(symbol=symbolslist)
    names_info = cmcinfo.data
    names = []
    for ind in names_info:
        names.append(names_info[ind]['name'].replace('[', '').replace(']', '').replace('(', '') .replace(')', ''))
        
    sorted.insert(1, "name", names)
    #sorted['names'] = names

    return sorted

#format (symbol, interval, 120 mins ago, now) or (symbol, interval, start date, end date) "1 Dec, 2017"
def getminutedata(symbol, interval, start, end):
    if(end == 'now'):
        # try:
        frame = pd.DataFrame(client.get_historical_klines(symbol,
                                                        interval,
                                                        start + ' min ago UTC'))
        # except:
        #     time.sleep(60)
        #     frame = pd.DataFrame(client.get_historical_klines(symbol,
        #                                                 interval,
        #                                                 start + ' min ago UTC'))
    else:
        # try:
        frame = pd.DataFrame(client.get_historical_klines(symbol, 
                                                        interval, 
                                                        start, 
                                                        end))
        # except:
        #     time.sleep(60)
        #     frame = pd.DataFrame(client.get_historical_klines(symbol, 
        #                                                 interval, 
        #                                                 start, 
        #                                                 end))     
    frame = frame.iloc[:,:6]                                                    
    frame.columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume']
    frame = frame.set_index('Time')
    frame.index = pd.to_datetime(frame.index, unit= 'ms')
    frame = frame.astype(float)
    return frame

def get_trends_3(coin):
    pytrends = TrendReq(hl='en-GB')
    data = pytrends.get_historical_interest(coin, 
                                    year_start=2021, 
                                    month_start=10, 
                                    day_start=4, 
                                    hour_start=0, 
                                    year_end=2021, 
                                    month_end=11, 
                                    day_end=22, 
                                    hour_end=23, 
                                    cat=0, 
                                    geo='', 
                                    gprop='', 
                                    sleep=0)
    data = data.drop('isPartial', axis=1)
    return data

def plot_coins(coin, HYPE, CLOSE):
    plt.figure(coin[1][0])
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
    plt.title(coin[1])
    plt.show(block=False)




def backtest(HYPE, CLOSE, minbuy, minsell):
    HYPE['diff'] = HYPE.iloc[:, 0].diff(periods=1)
    HYPE['Buy'] = (HYPE['diff'] > minbuy)
    HYPE['Sell'] = (HYPE['diff'] < minsell)
    HYPE['Close'] = CLOSE
    HYPE['Upward'] = HYPE['Close'].diff(periods=2)
    
    
    #print(HYPE)
    nHype = HYPE.to_numpy()
    holding = False
    buyprice = 0
    sellprice = 0
    tradeBuy = []
    tradeSell = []
    buyTime = []
    sellTime = []
    for row in range(len(nHype)):
        if ( (holding == False) and (nHype[row][2] == True) and (nHype[row][5] >= 0) ):
            buyprice = nHype[row][4]
            buyTime.append(nHype[row][0])
            holding = True

        if (holding == True and nHype[row][3] == True):
            sellprice = nHype[row][4]
            tradeBuy.append(buyprice)
            tradeSell.append(sellprice)
            sellTime.append(nHype[row][0])
            holding = False

    tradeDiff = []
    tradePerc = []

    for x in range(len(tradeBuy)-1):
        tradeDiff.append(tradeSell[x] - tradeBuy[x])
        tradePerc.append(tradeSell[x]/tradeBuy[x])

    tradeReturn = 1
    for x in tradePerc:
        tradeReturn *= x

    #print('Trade sums = ' + str(tradeDiff) )
    #print('Trade p/l% = ' + str(tradePerc) )
    result = []
    result.append( 'Hold Return = ' + str(HYPE['Close'][-1]/HYPE['Close'][0]) + '   Bot Return = ' + str(tradeReturn) )
    result.append( [tradePerc, buyTime, sellTime] )
    return result
    


############################## MAIN CODE ################################



#testcoins = [ ['LRCUSDT', ['Loopring']], ['FTMUSDT', ['Fantom']], ['MINAUSDT', ['Mina']], ['NEARUSDT', ['NEAR Protocol']], ['ZECUSDT', ['Zcash']], ['LTOUSDT', ['LTO network']], ['WNXMUSDT', ['Wrapped NXM']], ['DUSKUSDT', ['Dusk Network']], ['IOTXUSDT', ['IoTeX']], ['IDEXUSDT', ['IDEX']],  ['LRCUSDT', ['Loopring']]]

testcoins = [ ['BLZUSDT', ['Bluzelle']], ['BTSUSDT', ['BitShares']] ]



tradedata = []
for coin in testcoins:
    #time = str((60*24*7*10)+3)
    time_var = str(60*24*((7*6)))
    try:
        CLOSE = getminutedata(coin[0], '1m', time_var, 'now')['Close']
    except:
        print(coin[1][0])
        print('Error fetching minute data, check coin exists before time start')
        continue
        
    HYPE = get_trends_3(coin[1])

    plot_coins(coin, HYPE, CLOSE)

plt.show()

# change the diff data range, 1,2,3...

#show average trade times , how many of these would happen simulatenously, print out number of tradse, average p/l%, average holding time