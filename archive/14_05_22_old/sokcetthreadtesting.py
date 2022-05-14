from sys import displayhook
from binance.client import Client
from binance.enums import *
import pandas as pd
import time
from datetime import datetime
from sqlalchemy import create_engine
import numpy as np
from math import log10
from binance import BinanceSocketManager
import logging
import threading
import time
import asyncio

api_key = 'ihvXWbHvvDrYuroIJOS9ANW6X7tv5OQSYibLLloKyIGui0w93Q5yUJOBZclnNL5D'
api_secret = 'uzmKBJ3lmVS4TsTl2AOHVJOYTFfLM5qrg00vAqUyTYbSjiy7BDPlTpaq2Oy7qdo2'
client = Client(api_key, api_secret)
bsm = BinanceSocketManager(client)

db_data = 'mysql+mysqldb://' + 'admin' + ':' + '0323A8E3DB' + '@' + 'coin-database-1-instance-1.c9hqcydvu19f.us-east-1.rds.amazonaws.com' + ':3306/' + 'crypto_db' + '?charset=utf8mb4'
engine = create_engine(db_data)
date_recent_checked = "2022-04-25 23:00"
trend_table_rowcount_old = 100
def createframe(msg):
    df = pd.DataFrame([msg]) 
    df = df.loc[:,['s', 'E', 'p']]
    df.columns = ('symbol' , 'Time', 'Price') 
    df.Price = df.Price.astype(float) 
    df.Time = pd.to_datetime(df.Time, unit='ms') 
    return df

async def buysocket(ticker, buy_amt, SL=0.99, Target=1.01, open_position=False):
    print("in socket")
    socket = bsm.trade_socket(ticker)
    order = client.create_order(symbol=ticker, side='BUY', type='MARKET', quantity=buy_amt)
    buyprice = float(order['fills'][0]['price'])
    open_position = True
    while open_position:
        await socket.__aenter__()
        msg = await socket.recv()
        df = createframe(msg)
        #print(f'close = {df.Price.values}; target = {buyprice * Target}; stop = {buyprice * SL}')
        # print(f'target = {buyprice * Target}')
        # print(f'stop = {buyprice * SL}')
        if df.Price.values <= buyprice * SL  or df.Price.values >= buyprice * Target:
            order = client.create_order(symbol=ticker, side='BUY', type='MARKET', quantity=buy_amt)
            print(order)
            break

format = "%(asctime)s: %(message)s"
logging.basicConfig(format=format, level=logging.INFO,datefmt="%H:%M:%S")

def bg_async(func, thread_id):
    def wrapper():
        loop = asyncio.new_event_loop()
        loop.run_until_complete(func)
        # global holding
        #     if holding[thread_id]:
        #         break
    threading.Thread(target=wrapper).start()


def main():
    waiting = True
    check_data = False
    first = True
    while(True):
        if(waiting):
            trend_table_status = pd.read_sql_query("show table status like 'crypto_trend'", engine)
            trend_table_rowcount_new = trend_table_status['Rows'].values[0]
            if (trend_table_rowcount_new > trend_table_rowcount_old):
                check_data = True
                waiting = False
            else:
                time.sleep(5)
                #await asyncio.sleep(5)


        if(check_data):
            logging.info("algo    : pre sleep")
            time.sleep(5)
            logging.info("algo    : post sleep")
            if first:
                #thread = threading.Thread(target=asyncio.run, args=(buysocket('BTCUSDT', 0.0005),))
                thread_id = 1
                threading.Thread(target=asyncio.get_event_loop().run_until_complete, args=(buysocket('BTCUSDT', 0.0005),))
               
                logging.info("Main    : before running thread")
                
                #bg_async(buysocket('BTCUSDT', 0.0005), thread_id)
                thread.start()
                logging.info("Main    : after running thread")
                first = False
            check_data = False
            waiting = True
            
main()