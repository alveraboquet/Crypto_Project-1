from sys import displayhook
from binance.client import Client
from binance.enums import *
import pandas as pd
import time
from datetime import datetime
from sqlalchemy import create_engine
import numpy as np

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

if __name__ == "__main__":

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
    buy_ids = []
    buy_threshold = 80
    sell_threshold = 10


    waiting = True
    check_data = False
    # need async here? or while loop with 2 functions
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
                    value = getminutedata(crypto_table.loc[crypto_table['id'] == crypto_id]['ticker'].values[0], 
                                                        '15m',
                                                        '120')
                    close = value[['Time','Close']]                             
                    close.index = pd.to_datetime(close['Time'])
                    close = close.drop(columns=['Time'])
                    close = close.rename(columns={"Close": f"{crypto_id}"})
                    
                    if close.empty:
                        print(f"Close emtpy for id {crypto_id} at buy at {date_last_checked} - {date_recent_checked}")
                    else:
                        if (key != 0):
                            closes = closes.join(close)
                        else:
                            closes = close

                if(closes.empty):
                    continue
            
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
                        ticker = tickerdict[id]
                        key = full_id_list.index(id)
                        buyPrice[key] = float(client.get_symbol_ticker(symbol=ticker)['price'])
                        buyTime[key] = datetime.now().replace(microsecond=0)
                        holding[key] = True
                        print(f"Purchased {crypto_table.loc[crypto_table['id'] == id]['ticker'].values[0]} id {id}  at {buyPrice[key]} - {buyTime[key]}")
                    else:
                        continue
            # Sell control
            if (sell_ids):
                for id in sell_ids:
                    ticker = tickerdict[id]
                    # Sell execute function binance using ticker
                    key = full_id_list.index(id)
                    
                    sellPrice[key] = float(client.get_symbol_ticker(symbol=ticker)['price'])
                    sellTime[key] = datetime.now().replace(microsecond=0)
                    print(f"Trade completed: {crypto_table.loc[crypto_table['id'] == id]['ticker'].values[0]} id = {id} | open = {buyPrice[key]} at {buyTime[key]} | close = {sellPrice[key]} at {sellTime[key]} | profit = {(sellPrice[key]/buyPrice[key])}%")

                    # upload to database
                    quantity = 0
                    trade = (id, str(buyTime[key]), buyPrice[key], str(sellTime[key]), sellPrice[key], str(sellTime[key] - buyTime[key]),  sellPrice[key]/buyPrice[key], quantity)
                    index_names = ['crypto_id', 'date_buy', 'price_buy', 'date_sell', 'price_sell', 'trade_time', 'trade_return', 'quantity']
                    result = pd.DataFrame([trade],columns=index_names)
                    result.to_sql("crypto_trades_ev2", engine, if_exists="append", index=False)
                    # tradedata.append([id, buyTime[key], sellTime[key], buyPrice[key], sellPrice[key], (sellPrice[key]/buyPrice[key]) ])
                    holding[key] = False

            check_data = False
            waiting = True
            # Calculate profit
            # tradedata = np.array(tradedata)
            # scaled = ((tradedata[:,5] - 1) * 1/maxholds) + 1
            # scaled.prod()