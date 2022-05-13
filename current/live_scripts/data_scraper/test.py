
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
    
    print(header)