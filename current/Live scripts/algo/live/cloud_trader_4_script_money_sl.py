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

def getminutedata(symbol, interval, start):
    frame = pd.DataFrame(client.get_historical_klines(symbol,
                                                        interval,
                                                        start + ' min ago UTC'))
    frame = frame.iloc[:,:6]                                                    
    frame.columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume']
    frame = frame.set_index('Time')
    frame.index = pd.to_datetime(frame.index, unit= 'ms')
    frame = frame.astype(float)
    return frame.reset_index()

def createframe(msg):
    df = pd.DataFrame([msg]) 
    df = df.loc[:,['s', 'E', 'p']]
    df.columns = ('symbol' , 'Time', 'Price') 
    df.Price = df.Price.astype(float) 
    df.Time = pd.to_datetime(df.Time, unit='ms') 
    return df

async def buysocket(ticker, buy_amt, SL=0.99, Target=1.01, open_position=False):
    bsm = BinanceSocketManager(client)
    logging.info(f"Buy socket started for {ticker}")
    socket = bsm.trade_socket(ticker)
    order = client.create_order(symbol=ticker, side='BUY', type='MARKET', quantity=buy_amt)
    buyprice = float(order['fills'][0]['price'])
    open_position = True
    while open_position:
        if float(client.get_asset_balance(asset=ticker[:-4])['free']) < buy_amt:
            break
        try:
            await socket.__aenter__()
            msg = await socket.recv()
            df = createframe(msg)
            #print(f'close = {df.Price.values}; target = {buyprice * Target}; stop = {buyprice * SL}')
            # print(f'target = {buyprice * Target}')
            # print(f'stop = {buyprice * SL}')
            if df.Price.values <= buyprice * SL:  #or df.Price.values >= buyprice * Target:
                order = client.create_order(symbol=ticker, side='SELL', type='MARKET', quantity=buy_amt)
                logging.info(f"Buy socket ended succesfully for {ticker}")
                print(order)
                break
            else:
                await asyncio.sleep(2)
        except:
            logging.info(f"Buy socket ended /^\ for {ticker}")
            break

    for task in asyncio.Task.all_tasks():
        task.cancel()
    return 0


if __name__ == "__main__":
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO,datefmt="%H:%M:%S")
    api_key = 'ihvXWbHvvDrYuroIJOS9ANW6X7tv5OQSYibLLloKyIGui0w93Q5yUJOBZclnNL5D'
    api_secret = 'uzmKBJ3lmVS4TsTl2AOHVJOYTFfLM5qrg00vAqUyTYbSjiy7BDPlTpaq2Oy7qdo2'
    client = Client(api_key, api_secret)
    db_data = 'mysql+mysqldb://' + 'admin' + ':' + '0323A8E3DB' + '@' + 'coin-database-1-instance-1.c9hqcydvu19f.us-east-1.rds.amazonaws.com' + ':3306/' + 'crypto_db' + '?charset=utf8mb4'
    engine = create_engine(db_data)

    check_date = pd.read_sql_query("SELECT MAX(date_request) FROM crypto_trend", engine) 
    date_recent_checked = str(check_date.iloc[0, 0])

    trend_table_status = pd.read_sql_query("show table status like 'crypto_trend'", engine)
    trend_table_rowcount_old = trend_table_status['Rows'].values[0]

    cryptoString = 'SELECT * FROM crypto'
    crypto_table = pd.read_sql_query(cryptoString, engine)
    full_id_list = crypto_table.id.astype(int).tolist()
    tickerdict = pd.Series(crypto_table.ticker.values,index=crypto_table.id).to_dict()
    
    #setup variables
    maxholds = 3
    trades = [[],[],[],[]]
    tradedata = []
    buyPrice  = [0] * (len(full_id_list))
    sellPrice = [0] * (len(full_id_list))
    tradeBuy  = [0] * (len(full_id_list))
    tradeSell = [0] * (len(full_id_list))
    buyTime   = [0] * (len(full_id_list))
    sellTime  = [0] * (len(full_id_list))
    holding = [False] * (len(full_id_list))
    qty = [0] * (len(full_id_list))
    buy_ids = []
    buy_threshold = 70
    sell_threshold = 80


    waiting = True
    check_data = False
   
    while(True):

        if(waiting):
            if datetime.now().minute < 20:
                trend_table_status = pd.read_sql_query("show table status like 'crypto_trend'", engine)
                trend_table_rowcount_new = trend_table_status['Rows'].values[0]
                if (trend_table_rowcount_new > trend_table_rowcount_old):
                    check_data = True
                    waiting = False
                else:
                    time.sleep(5)
            else:
                time.sleep(60)

        if(check_data):
            date_last_checked = date_recent_checked
            new_trends_string = f"SELECT * FROM crypto_trend WHERE date_request > '{date_last_checked}' ORDER BY date_request, crypto_id, date"
            new_trends = pd.read_sql_query(new_trends_string, engine)
            #update to ensure that if the count increased inbetween the request for count and request for data, does not re-check
            trend_table_rowcount_old = pd.read_sql_query("show table status like 'crypto_trend'", engine)['Rows'].values[0]

            if new_trends.empty:
                print(f"Dataframe empty for request: {new_trends_string}")
                check_data = False
                waiting = True
                continue

            date_recent_checked = new_trends.date_request.max()

            try:
                trends = new_trends.pivot(index="date", columns="crypto_id", values="hype") #unbeliiiiieveevevevable !! https://pandas.pydata.org/pandas-docs/stable/user_guide/reshaping.html
            except:
                pd.set_option("display.max_rows", None, "display.max_columns", None)
                print(new_trends)
                continue

            #check buying and selling conditions
            check_100 = ((trends.iloc[-2] == 100))# | (trends.iloc[-1] == 100)) ##check trends with current time
            check_non0 = trends.iloc[0:-2].mean() > 7 
            check_peak = (trends.iloc[0:-10] < buy_threshold).all()
            trend_indicate_buy = np.logical_and.reduce((check_100, check_non0, check_peak), dtype=bool)

            curr_id_list = trends.columns.values
            check_upward_ids = [curr_id_list[i] for i in [i for i, x in enumerate(trend_indicate_buy) if x]]
            
            buy_ids = []
            if check_upward_ids:
                print(f"Indicate buy ids: {check_upward_ids} between {date_last_checked} : {date_recent_checked}")
                for key, crypto_id in enumerate(check_upward_ids):
                    try:
                        value = getminutedata(crypto_table.loc[crypto_table['id'] == crypto_id]['ticker'].values[0], 
                                                        '15m',
                                                        '120')
                    except:
                        print( f"ticker {crypto_table.loc[crypto_table['id'] == crypto_id]['ticker']} outdated" )
                        continue
                    close = value[['Time','Close']]                             
                    close.index = pd.to_datetime(close['Time'])
                    close = close.drop(columns=['Time'])
                    close = close.rename(columns={"Close": f"{crypto_id}"})
                    
                    if (key != 0):
                        closes = closes.join(close)
                    else:
                        closes = close
            
                increase = closes.diff(periods=6)
                check_increase = (increase.iloc[-1] >= 0)

                indicate_buy = check_increase[check_increase].index.values.astype(int)
                #print(f"Indicate buy ids: {indicate_buy} between {date_last_checked} : {date_recent_checked}")

                curr_NOT_holding_ids = [full_id_list[i] for i in [i for i, x in enumerate(np.logical_not(holding)) if x]]
                buy_ids = list(set(indicate_buy).intersection(curr_NOT_holding_ids))
            
            check_decrease = np.logical_or((trends.iloc[-1] < sell_threshold), (trends.iloc[-2] < sell_threshold))
            indicate_sell = check_decrease[check_decrease].index.values.astype(int)
            #print(f"Indicate sell ids: {indicate_sell} between {date_last_checked} : {date_recent_checked}")

            curr_holding_ids = [full_id_list[i] for i in [i for i, x in enumerate(holding) if x]]
            sell_ids = list(set(indicate_sell).intersection(curr_holding_ids))

            
            # Buy control
            if ((sum(holding) < maxholds) and buy_ids):
                for id in buy_ids:
                    if (sum(holding) < maxholds):
                        key = full_id_list.index(id)
                        ticker = tickerdict[id]

                        ################################################
                        currbal = float(client.get_asset_balance(asset='USDT')['free'])
                        buy_amt = round( currbal / (maxholds - sum(holding)), 2)
                        buy_amt = 100

                        liveprice = float(client.get_symbol_ticker(symbol=ticker)['price'])
                        qty_pre = (buy_amt)/liveprice
                        pricePrecision = -log10(float(client.get_symbol_info(ticker)['filters'][2]['stepSize']))
                        qty[id] = round(qty_pre, int(pricePrecision))
                        #################################################
                        # buyorder = client.create_order(symbol=ticker,
                        #                                 side='BUY',
                        #                                 type='MARKET',
                        #                                 quantity = qty[id])

                        # buyorder = client.create_order(symbol = ticker, 
                        #                             side = 'BUY', 
                        #                             type = ORDER_TYPE_STOP_LOSS,
                        #                             quantity = qty[id],
                        #                             stopPrice = float(liveprice)*0.99)
                        
                        #threading.Thread(target=asyncio.get_event_loop().run_until_complete, args=(buysocket(ticker, qty[id]),))
                        threading.Thread(target=asyncio.run, args=(buysocket(ticker, qty[id]),)).start()
                        holding[key] = True
                        buyPrice[key] = liveprice
                        buyTime[key] = datetime.now().replace(microsecond=0)
                        
                        #market_price = float(buyorder['fills'][0]['price'])
                        market_price = 'na'

                        #print(buyorder)

                        ####################################################
                        print(f"Purchased {ticker} id {id}  at {buyPrice[key]} (marketprice = {market_price}) - {buyTime[key]}")
                    else:
                        continue
            # Sell control
            if (sell_ids):
                for id in sell_ids:
                    ticker = tickerdict[id]
                    # Sell execute function binance using ticker
                    key = full_id_list.index(id)
                    sellTime[key] = datetime.now().replace(microsecond=0)
                    ###############################
                    holding_amount = client.get_asset_balance(asset=ticker[:-4])['free']
                    if float(holding_amount) != 0:
                        sellorder = client.create_order(symbol=ticker,
                                side='SELL', 
                                type= 'MARKET', 
                                quantity = qty[id])
                        market_price = float(sellorder['fills'][0]['price'])
                        sellPrice[key] = market_price
                        holding[key] = False
                        print(sellorder)
                    else:
                        sellPrice[key] = 0.99 * buyPrice[key]
                        holding[key] = False
                        print("stop loss triggered")
                    ##################################
                    print(f"Trade completed: {ticker} id = {id} | open = {buyPrice[key]} at {buyTime[key]} | close = {sellPrice[key]} at {sellTime[key]} | profit = {(sellPrice[key]/buyPrice[key])}%  (marketprice = {market_price})")

                    # upload to database
                    trade = (id, str(buyTime[key]), buyPrice[key], str(sellTime[key]), sellPrice[key], str(sellTime[key] - buyTime[key]),  sellPrice[key]/buyPrice[key], buy_amt)
                    index_names = ['crypto_id', 'date_buy', 'price_buy', 'date_sell', 'price_sell', 'trade_time', 'trade_return', 'quantity']
                    result = pd.DataFrame([trade],columns=index_names)


                    #########################
                    result.to_sql("crypto_trades_ev3", engine, if_exists="append", index=False)
                    ##########################


                    # tradedata.append([id, buyTime[key], sellTime[key], buyPrice[key], sellPrice[key], (sellPrice[key]/buyPrice[key]) ])
                    

            check_data = False
            waiting = True
            # Calculate profit
            # tradedata = np.array(tradedata)
            # scaled = ((tradedata[:,5] - 1) * 1/maxholds) + 1
            # scaled.prod()