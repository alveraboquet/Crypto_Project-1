from pytrends.request import TrendReq
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.dates as mdates





def get_trends_1():
    plt.style.use('ggplot')
    plt.rcParams["figure.figsize"] = (40,20)
    pytrends = TrendReq(hl='en-GB')
    all_keywords = [['hertz network'],['decentraland'],['elonomics']]
    keywords = []
    timeframes = ['today 5-y', 'today 12-m', 'today 3-m', 'today 1-m',
                'now 7-d', 'now 1-d', 'now 4-H']
    cat = '0'
    geo = ''
    gprop = ''
    for kw in range(len(all_keywords)):
        pytrends.build_payload(all_keywords[kw],
                               cat,
                               timeframes[4],
                               geo,
                               gprop)
        data = pytrends.interest_over_time()
        data = data.drop('isPartial', axis=1)
        #print(data)
        plt.figure(kw)
        #print(all_keywords[kw])
        plt.plot(data)
        plt.plot(data.rolling(10).mean())
        plt.legend(all_keywords[kw])
        plt.xlabel("Date & Time")
        plt.ylabel("Interest")
        plt.show(block=False)

def get_trends_2():
    plt.style.use('ggplot')
    plt.rcParams["figure.figsize"] = (40,20)
    pytrends = TrendReq(hl='en-GB')
    all_keywords = [['hertz network'],['decentraland'],['elonomics']]

    for kw in range(len(all_keywords)):
        data = pytrends.get_historical_interest(all_keywords[kw], 
                                 year_start=2021, 
                                 month_start=11, 
                                 day_start=9, 
                                 hour_start=0, 
                                 year_end=2021, 
                                 month_end=11, 
                                 day_end=14, 
                                 hour_end=19, 
                                 cat=0, 
                                 geo='', 
                                 gprop='', 
                                 sleep=60)
        data = data.drop('isPartial', axis=1)
        #print(data)
        plt.figure(kw)
        #print(all_keywords[kw])
        plt.plot(data)
        plt.plot(data.rolling(10).mean())
        plt.legend(all_keywords[kw])
        plt.xlabel("Date & Time")
        plt.ylabel("Interest")
        plt.show(block=False)


def get_trends_3():
    pytrends = TrendReq(hl='en-GB')
    data = pytrends.get_historical_interest(['hertz network'], 
                                    year_start=2021, 
                                    month_start=11, 
                                    day_start=9, 
                                    hour_start=0, 
                                    year_end=2021, 
                                    month_end=11, 
                                    day_end=14, 
                                    hour_end=23, 
                                    cat=0, 
                                    geo='', 
                                    gprop='', 
                                    sleep=0)
    data = data.drop('isPartial', axis=1)
    print(data)


#get_trends_1()

#get_trends_2()

#plt.show()

get_trends_3()
