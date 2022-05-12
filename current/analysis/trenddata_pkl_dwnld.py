import pandas as pd
import datetime
from sqlalchemy import create_engine


db_data = 'mysql+mysqldb://' + 'admin' + ':' + '0323A8E3DB' + '@' + 'coin-database-1-instance-1.c9hqcydvu19f.us-east-1.rds.amazonaws.com' + ':3306/' + 'crypto_db' + '?charset=utf8mb4'
engine = create_engine(db_data)

start_string_close = "2022-03-01 12:00:00" 
start_string = "2022-03-01 14:00:00"
end_string = "2022-04-15 21:00:00"
start_date = datetime.datetime.strptime(start_string, '%Y-%m-%d %H:%M:%S')
end_date = datetime.datetime.strptime(end_string, '%Y-%m-%d %H:%M:%S')

new_trends_string = f"SELECT * FROM crypto_trend WHERE date_request > '{start_string}' AND date_request < '{end_string}' ORDER BY date_request, crypto_id, date"
new_trends_all = pd.read_sql_query(new_trends_string, engine)

new_trends_all.to_pickle("new_trends_all_010322_150422.pkl") 