import pandas as pd
import time
import websocket
import json, pprint, talib 
import numpy
import csv

from binance.client import Client
from binance.enums import *
from coinmarketcapapi import CoinMarketCapAPI, CoinMarketCapAPIError

from pytrends.request import TrendReq as UTrendReq
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.dates as mdates

headers = {
    'authority': 'trends.google.com',
    'sec-ch-ua': '"Chromium";v="94", " Not A;Brand";v="99", "Opera";v="80"',
    'accept': 'application/json, text/plain, */*',
    'sec-ch-ua-mobile': '?0',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36 OPR/80.0.4170.63',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-mode': 'cors',
    'sec-fetch-dest': 'empty',
    'referer': 'https://trends.google.com/trends/explore?q=mirror%20protocol',
    'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    'cookie': '__utmc=10102256; __utma=10102256.830189433.1636580671.1637612468.1637615437.6; __utmz=10102256.1637615437.6.4.utmcsr=google|utmccn=(organic)|utmcmd=organic|utmctr=(not%20provided); __utmt=1; __utmb=10102256.9.9.1637615792660; CONSENT=YES+GB.en-GB+V9+BX; SEARCH_SAMESITE=CgQImZMB; HSID=A0PbYKwoJWHkP2cLJ; SSID=ATw-D_CgCgaCnOMxq; APISID=hng8MXyBWur_w5fC/AurWCgPbsYDEtwkWm; SAPISID=vSGlu5opiC_3-Dav/Ak0loYtHrjyKusKXH; __Secure-1PAPISID=vSGlu5opiC_3-Dav/Ak0loYtHrjyKusKXH; __Secure-3PAPISID=vSGlu5opiC_3-Dav/Ak0loYtHrjyKusKXH; OGPC=19025836-2:; __Secure-1PSIDCC=AJi4QfHJF0V84yFFydIeqwcTavYgTxPKZTm4r-j92P2vuN691-chSFUrnLeYq4ccPLlok1ebJg; SID=EAgztJro1wlVbGdfzKYVqqxGYz9eHXx7y-0pWf9ljDCqShG7I4iq_DUrjYYzifOFgAkPdg.; __Secure-1PSID=EAgztJro1wlVbGdfzKYVqqxGYz9eHXx7y-0pWf9ljDCqShG7Arm0dTwN1pVkMU_W42hVkA.; __Secure-3PSID=EAgztJro1wlVbGdfzKYVqqxGYz9eHXx7y-0pWf9ljDCqShG7J8Mh2faUlqm65EfZ7UsPCQ.; NID=511=esdr8y2puX552h2JBc-TknP1obzsr3qLgSA0yeAV7DnfwAVYC251PzaCr4yYLsm0EyMjI7L7neOP6JTtPSHjnHgitlzfoWrzX7xcm8n8hB6wIeLNCMeECr-IhEQs3-ocHCofs6pbgR6LwfrvhIvF9WCClueXUX4FKGD3CQ14xkM9ikLu44rqvJjgYtyXfcwcFl3qpWZOKGfuY4Jz_Molfk7bNBlNNaNUe0CeMlei3I4dIkHbEBlAA6LW8vFhnIZyMWhCd2lVkAiy0c_FOaUUp7iCKPUj6RD-ddXs7X_j7X5-2DRkXkUZI5Cl8d-ZyyPWDGcnOtvPGwBiTGQ8o7tRxRMRMjjR_cnrR9TyMUIdYJ7F7cJmTl9GUqgZ-spxHWzUU0hlgmrdLErIBsTdXA; 1P_JAR=2021-11-22-21; SIDCC=AJi4QfHp9yLbArD3EA6819JHREwwDTB9vLz-bkPMpDjk7VY2Zh26Zb4JTNu7jl3FkmbY6CEZeL18; __Secure-3PSIDCC=AJi4QfEct8ZkJckjPrd7cpR-xm748VcgUsitncJ7DEkOKMdTbMOZSwaZbCxEyvinm2nCvqQ-3rQ3',
}

GET_METHOD='get'
class TrendReq(UTrendReq):
    def _get_data(self, url, method=GET_METHOD, trim_chars=0, **kwargs):
        return super()._get_data(url, method=GET_METHOD, trim_chars=trim_chars, headers=headers, **kwargs)


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
    non_stable_rm = non_stable_rm.drop( non_stable_rm[non_stable_rm.symbol == 'BUSDUSDT'].index ) # Binance USD
    non_stable_rm = non_stable_rm.drop( non_stable_rm[non_stable_rm.symbol == 'BTGUSDT'].index ) # Bitcoin Gold
    non_stable_rm = non_stable_rm.drop( non_stable_rm[non_stable_rm.symbol == 'ERDUSDT'].index ) # Elrond (ERD) Mainnet & Token Swap to Elrond Gold (EGLD) 
    non_stable_rm = non_stable_rm.drop( non_stable_rm[non_stable_rm.symbol == 'LENDUSDT'].index ) # LEND Token Swap to AAVE
    non_stable_rm = non_stable_rm.drop( non_stable_rm[non_stable_rm.symbol == 'MCOUSDT'].index ) # MCO Token unsupported

    non_stable_rm = non_stable_rm.drop( non_stable_rm[non_stable_rm.symbol == 'GXSUSDT'].index ) # Find a way to replace lookup
    non_stable_rm = non_stable_rm.drop( non_stable_rm[non_stable_rm.symbol == 'IOTAUSDT'].index ) # Find a way to replace lookup

    non_stable_rm = non_stable_rm.drop( non_stable_rm[non_stable_rm.symbol == 'NPXSUSDT'].index ) # Pundi X old -> PUNDIX
    non_stable_rm = non_stable_rm.drop( non_stable_rm[non_stable_rm.symbol == 'PAXGUSDT'].index ) # Pax Gold Binance Completes VEN Mainnet Swap to VET
    non_stable_rm = non_stable_rm.drop( non_stable_rm[non_stable_rm.symbol == 'VENUSDT'].index ) # Binance Completes VEN Mainnet Swap to VET 
    non_stable_rm = non_stable_rm.drop( non_stable_rm[non_stable_rm.symbol == 'TUSDUSDT'].index ) # stable coin TrueUSD 
    non_stable_rm = non_stable_rm.drop( non_stable_rm[non_stable_rm.symbol == 'STORMUSDT'].index ) #Storm (STORM) Token Swap to STMX  NPXS	 
    non_stable_rm = non_stable_rm.drop( non_stable_rm[non_stable_rm.symbol == 'SUSDUSDT'].index ) # usd coin sUSD
    # symbols = symbols.replace('GXS', 'GXC')
    # symbols = symbols.replace('IOTA', 'MIOTA')


    #sorted = non_stable_rm.sort_values(by='priceChangePercent', ascending=False)
    sorted = non_stable_rm.sort_values(by='symbol', key=lambda x: x.str.split('USDT').str[0])

    token_tickers = sorted
    symbols=token_tickers['symbol'].str.slice(0,-4)
    # symbols = symbols.replace('GXS', 'GXC')
    # symbols = symbols.replace('IOTA', 'MIOTA')
    symbolslist = ",".join(symbols)

    cmcinfo = cmc.cryptocurrency_info(symbol=symbolslist)
    names_info = cmcinfo.data
    names = []
    for ind in names_info:
        names.append(names_info[ind]['name'].replace('[', '').replace(']', '').replace('(', '') .replace(')', ''))
        
    sorted.insert(1, "name", names)

    alltokens = sorted[['symbol', 'name']]
    
    #sorted['names'] = names

    return alltokens.reset_index().rename({'index': 'Binance Index'}, axis=1)

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
    return frame[['Close', 'Volume']]

def get_trends_3(coin):
    pytrends = TrendReq(hl='en-GB', timeout=(10,25))
    data = pytrends.get_historical_interest(coin, 
                                    year_start=2021, 
                                    month_start=9, 
                                    day_start=1, 
                                    hour_start=0, 
                                    year_end=2021, 
                                    month_end=11, 
                                    day_end=22, 
                                    hour_end=23, 
                                    cat=0, 
                                    geo='', 
                                    gprop='', 
                                    sleep=0)
    if 'isPartial' in data:
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
    plt2.plot(HYPE.diff(periods=2))
    plt2.set_ylabel("Hype %")
    plt2.legend(['Close price'])
    plt.legend(['Buy Indicator', 'Rolling indicator 5 + 20%', 'Rolling indicator 5', 'differential 1', 'differential 2'])
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