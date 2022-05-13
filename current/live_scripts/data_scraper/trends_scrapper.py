import pandas as pd
import time
from datetime import datetime, timedelta
import numpy as np
import sys
from pytrends.request import TrendReq as UTrendReq
from binance.client import Client
from binance.enums import *
from sqlalchemy import create_engine


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Use as: 'trends_scrapper.py {instance number} {start id} {end id}'")
    headername = int(sys.argv[1])
    start_id = int(sys.argv[2])
    end_id = int(sys.argv[3])
    
    if headername == 1:
        from trends_headers import chrome_home as header
    if headername == 2:
        from trends_headers import sondrel as header
    if headername == 3:
        from trends_headers import david as header
    if headername == 4:
        from trends_headers import edjacob as header
    if headername == 5:
        from trends_headers import max as header
    if headername == 6:
        from trends_headers import sondhotspot as header
    if headername == 7:
        from trends_headers import edge as header
    if headername == 8:
        from trends_headers import edgeincog as header
    if headername == 9:
        from trends_headers import operavpninvog as header
    

    GET_METHOD='get'
    class TrendReq(UTrendReq):
        def _get_data(self, url, method=GET_METHOD, trim_chars=0, **kwargs):
            return super()._get_data(url, method=GET_METHOD, trim_chars=trim_chars, headers=header, **kwargs)

    def get_trends_live(coin):
        #headers = header_useragent
        pytrends = TrendReq(hl='en-GB')
        pytrends.build_payload([coin], timeframe='now 7-d')
        trend = pytrends.interest_over_time()
        return trend


    api_key = 'ihvXWbHvvDrYuroIJOS9ANW6X7tv5OQSYibLLloKyIGui0w93Q5yUJOBZclnNL5D'
    api_secret = 'uzmKBJ3lmVS4TsTl2AOHVJOYTFfLM5qrg00vAqUyTYbSjiy7BDPlTpaq2Oy7qdo2'
    client = Client(api_key, api_secret)


    db_data = 'mysql+mysqldb://' + 'admin' + ':' + '0323A8E3DB' + '@' + 'coin-database-1-instance-1.c9hqcydvu19f.us-east-1.rds.amazonaws.com' + ':3306/' + 'crypto_db' + '?charset=utf8mb4'
    engine = create_engine(db_data)

    cryptoString = 'SELECT * FROM crypto'
    crypto_table = pd.read_sql_query(cryptoString, engine)
    id_list_pre = crypto_table.id.astype(int).tolist()
    id_list_pre.remove(226)
    id_list = id_list_pre[start_id-1:end_id-1]
    success_count = 0

    date_request_start = datetime.now().replace(microsecond=0)

    for key, crypto_id in enumerate(id_list):
        #fetch date
        date_request = datetime.now().replace(microsecond=0)
        #try to fetch data

        try:
            trend = get_trends_live(crypto_table.loc[crypto_table['id'] == crypto_id]['name_searchable'].values[0]) #this might need to be crypto_table[id == crypto_id] ?? check how works
        except:
            print(f"{date_request}: {crypto_id} trend delay 1 min ")
            time.sleep(60)
            try:
                trend = get_trends_live(crypto_table.loc[crypto_table['id'] == crypto_id]['name_searchable'].values[0])
            except:
                print(f"{date_request}: {crypto_id} trend delay 5 min ")
                time.sleep(60*5)
                try:
                    #juggle headers???
                    trend = get_trends_live(crypto_table.loc[crypto_table['id'] == crypto_id]['name_searchable'].values[0])
                except:
                    print(f"{date_request}: {crypto_id} trend request failed at ")
                continue
        # if data is empty due to invalid name skip
        if trend.empty:
            print(f"{date_request}: {crypto_id} trend data not valid, check name_searchable")
            continue

        #format data
        trend = trend.drop(['isPartial'], axis=1)
        trend = trend.rename(columns={trend.columns[0]: "hype"})
        trend['crypto_id'] = crypto_id
        trend['date_request'] = date_request
        trend['date'] = pd.to_datetime(trend.index)
        trend = trend.reset_index(drop=True)

        #upload to database
        try:
            trend.to_sql("crypto_trend", engine, if_exists="append", index=False)
            success_count += 1
        except:
            print(f"{date_request}: {crypto_id} repeat data ")

        time.sleep(10)
    #print results
    print(f"{date_request_start}: Completed {success_count}/{end_id-start_id} requests")
    engine.dispose()