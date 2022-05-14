import pandas as pd
import time
import websocket
import json, pprint, talib 
import numpy
import csv
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import pickle

from binance.client import Client
from binance.enums import *
from coinmarketcapapi import CoinMarketCapAPI, CoinMarketCapAPIError

from pytrends.request import TrendReq as UTrendReq
import matplotlib.pyplot as plt
import numpy as np


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
    return frame[['Close']]

def get_trends_3(coin, start, end):
    pytrends = TrendReq(hl='en-GB')
    data = pytrends.get_historical_interest(coin, 
                                    year_start=start[3], 
                                    month_start=start[2], 
                                    day_start=start[1], 
                                    hour_start=start[0], 
                                    year_end=end[3], 
                                    month_end=end[2], 
                                    day_end=end[1], 
                                    hour_end=start[0], 
                                    cat=0, 
                                    geo='', 
                                    gprop='', 
                                    sleep=0)
    data = data.drop('isPartial', axis=1)
    return data


allCoin_df = get_all_tokens()

allCoin_array = allCoin_df.to_numpy()
allCoin_list = []
for x in range(len(allCoin_array)-1):
    allCoin_list.append([allCoin_array[x][1], [allCoin_array[x][2]]])

open_file = open("allCoin_list.pkl", "wb")
pickle.dump(allCoin_list, open_file)
open_file.close()

dayDelta = 0
monthDelta =-3
dt_end      = datetime.now()
dt_start    = (datetime.now() + relativedelta(months=monthDelta) + timedelta(days=dayDelta))
dt_ar_end   = list(map(int,   dt_end.strftime("%d-%m-%Y-%H-%M-%S").split('-') ))
dt_ar_start = list(map(int, dt_start.strftime("%d-%m-%Y-%H-%M-%S").split('-') ))
end         = [dt_ar_end[3],  dt_ar_end[0],  dt_ar_end[1],  dt_ar_end[2]]
start       = [dt_ar_end[3],dt_ar_start[0],dt_ar_start[1],dt_ar_start[2]]

# start = [0,21,11,2021]
# end = [0,21,11,2021]
#dt_start = datetime.datetime(start[3], start[2], start[1])
#dt_end   = datetime.datetime(  end[3],   end[2],   end[1])

time_delta = (dt_end - dt_start)
total_seconds = time_delta.total_seconds()
minutes = total_seconds/60
time_var = str(int(minutes))


coin = allCoin_list[0]

ALL_COIN = getminutedata(coin[0], '1m', time_var, 'now')  
ALL_HYPE = get_trends_3(coin[1], start, end)
ALL_COIN =  ALL_COIN.rename(columns={"Close": coin[0][:4]})
ALL_HYPE.index.names = ['Date']
ALL_COIN.index.names = ['Date']
ALL_COIN = ALL_COIN.merge(ALL_HYPE, how='outer', on='Date').ffill()
ALL_COIN.to_pickle("./COIN.pkl")
ALL_COIN.to_csv("./COIN.csv")

for coin in allCoin_list[1:]:
    COIN = getminutedata(coin[0], '15m', time_var, 'now')  
    HYPE = get_trends_3(coin[1], start, end)
    COIN =  COIN.rename(columns={"Close": coin[0][:4]})
    HYPE.index.names = ['Date']
    COIN.index.names = ['Date']
    ALL_COIN = ALL_COIN.merge(COIN, how='outer', on='Date')
    ALL_COIN = ALL_COIN.merge(HYPE, how='outer', on='Date').ffill()
    ALL_COIN.to_pickle("./coindata_6month.pkl")
    ALL_COIN.to_csv("./coindata_6month.csv")
    time.sleep(10)