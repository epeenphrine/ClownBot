import requests
import time
import config
## the daily price endpoint


'''this script is for getting prices. the prices are delayed by 15 minute. There are two functions here:
price_get and price_gets. price_get is used to get single ticker price and price_gets is used for multiple ticker.
 make sure to put your api key in config.py in tda_api variable'''

def price_get(ticker):
    #define our endpoint
    ticker = ticker.upper()
    endpoint = f"https://api.tdameritrade.com/v1/marketdata/{ticker}/quotes"
    print(endpoint)


    ## define our payload

    payload = {"apikey" : config.tda_api}

    ## make request

    content = requests.get(url=endpoint, params = payload)

    #3 convert it a dictionary

    data = content.json()
    data = data[ticker]
    bid = data["bidPrice"]
    ask = data["askPrice"]
    mid = float((ask + bid)/2)
    return mid

def price_gets(ticker):
    endpoint = 'https://api.tdameritrade.com/v1/marketdata/quotes'

    payload = {"apikey": config.tda_api,
               "symbol": f"{ticker}"}

    content = requests.get(url=endpoint, params=payload)

    data = content.json()
    tickers = []
    for item in data:
        tickers.append(item)
    mid_list = []
    for i in range(0, len(tickers)):
        datas = data[tickers[i]]
        bid = datas["bidPrice"]
        ask = datas["askPrice"]
        mid = float((bid+ask)/2)
        print(f"{tickers[i]} : {mid}")
        mid_list.append(mid)
    return mid_list
