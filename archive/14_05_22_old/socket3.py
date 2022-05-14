import asyncio
from threading import Thread
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
import time
import asyncio
import sys

def createframe(msg):
    df = pd.DataFrame([msg]) 
    df = df.loc[:,['s', 'E', 'p']]
    df.columns = ('symbol' , 'Time', 'Price') 
    df.Price = df.Price.astype(float) 
    df.Time = pd.to_datetime(df.Time, unit='ms') 
    return df

async def buysocket(ticker, buy_amt, SL=0.99, Target=1.01, open_position=False):
    api_key = 'ihvXWbHvvDrYuroIJOS9ANW6X7tv5OQSYibLLloKyIGui0w93Q5yUJOBZclnNL5D'
    api_secret = 'uzmKBJ3lmVS4TsTl2AOHVJOYTFfLM5qrg00vAqUyTYbSjiy7BDPlTpaq2Oy7qdo2'
    client = Client(api_key, api_secret)
    bsm = BinanceSocketManager(client)
    logging.info(f"Buy socket started for {ticker}")
    socket = bsm.trade_socket(ticker)
    order = client.create_order(symbol=ticker, side='BUY', type='MARKET', quantity=buy_amt)
    buyprice = float(order['fills'][0]['price'])
    open_position = True
    while open_position:
        print(client.get_asset_balance(asset=ticker[:-4])['free'])
        #try:
        if float(client.get_asset_balance(asset=ticker[:-4])['free']) < buy_amt:
            sys.exit()

        await socket.__aenter__()
        msg = await socket.recv()
        df = createframe(msg)
        print(f'close = {df.Price.values}; target = {buyprice * Target}; stop = {buyprice * SL}')
        # print(f'target = {buyprice * Target}')
        # print(f'stop = {buyprice * SL}')
        if df.Price.values <= buyprice * SL  or df.Price.values >= buyprice * Target:
            order = client.create_order(symbol=ticker, side='BUY', type='MARKET', quantity=buy_amt)
            logging.info(f"Buy socket ended succesfully for {ticker}")
            print(order)
            sys.exit()
        float(client.get_asset_balance(asset='USDT')['free'])
        #except:
        #    logging.info(f"Buy socket ended /^\ for {ticker}")


def bg_async(coro):
    def wrapper():
        loop = asyncio.new_event_loop()
        loop.run_until_complete(coro)
    
    Thread(target=wrapper).start()

def main_thread():
    bg_async(buysocket('BTCUSDT', 0.0005))


if __name__ == "__main__":
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO,datefmt="%H:%M:%S")
    api_key = 'ihvXWbHvvDrYuroIJOS9ANW6X7tv5OQSYibLLloKyIGui0w93Q5yUJOBZclnNL5D'
    api_secret = 'uzmKBJ3lmVS4TsTl2AOHVJOYTFfLM5qrg00vAqUyTYbSjiy7BDPlTpaq2Oy7qdo2'
    client = Client(api_key, api_secret)
    #bsm = BinanceSocketManager(client)
    Thread(target=main_thread).start()