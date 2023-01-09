import requests
import telebot
import time
import pandas as pd
from pandas import DataFrame

telebot_url = "https://api.telegram.org/bot"
telebot_token = ""
telebot_url += telebot_token
chat_id = ""

bot = telebot.TeleBot(telebot_token)


base_url = "https://testnet.binancefuture.com"
end_point_index_prices = "/fapi/v1/premiumIndex"
end_point_klines = "/fapi/v1/klines"


pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width',1000)

def to_buy_pr_change(coin_prices):
    to_buy_str = ""
    for i in coin_prices:
        if ((i['highest_price'] - i['index_price']) / i['highest_price']) * 100 > 7:
            to_buy_str += (i['name']) + ','
    if to_buy_str == "":
        return 'Price change: nothing to buy for now'
    else:
        return "Price change: possible to buy: " + to_buy_str.rstrip(to_buy_str[-1])


def to_sell_pr_change(coin_prices):
    to_sell_str = ""
    for i in coin_prices:
        if ((i['index_price'] - i['lowest_price']) / i['lowest_price']) * 100 > 7:
            to_sell_str += (i['name']) + ','
    if to_sell_str == "":
        return 'Price change: nothing to sell for now'
    else:
        return "Price change: possible to sell: " + to_sell_str.rstrip(to_sell_str[-1])

def buy_signal_macd(coin_prices, url, klines_end_point,interval):
    lim = 5
    to_buy_str = ""
    for i in coin_prices:
        symbol = i['name']
        r = requests.get(f"{url}{klines_end_point}?symbol={symbol}&interval={interval}&limit={lim}")
        df = DataFrame.from_dict(r.json()).iloc[:,:5]
        df.columns = list("tohlc")
        df['ma_fast'] = df['c'].ewm(span=12,adjust=False).mean()
        df['ma_slow'] = df['c'].ewm(span=26, adjust=False).mean()
        df['macd'] = df['ma_fast'] - df['ma_slow']
        df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['delta'] = df['macd'] - df['signal']
        eps = (i['index_price'] * 0.01)
        if df['delta'][lim-1] >= -eps and df['delta'][lim-1] <= eps:
            to_buy_str += i['name'] + ','
    if to_buy_str != "":
        return "MACD: possible to buy: " + to_buy_str.rstrip(to_buy_str[-1])
    else:
        return "MACD: nothing to buy for now"



coin_names = ["BTCUSDT", "XRPUSDT", "ADAUSDT", "ETHUSDT", "MKRUSDT", "XMRUSDT","LTCUSDT", "BNBUSDT","MASKUSDT","SUSHIUSDT"]
coin_prices = []
timeframe = "4h"
m = 60
h = 60*m
sending_interval = {
    '1h': 5*m,
    '4h': 30*m,
    '1d': 1*h,
    '1w': 12*h
}

for i in coin_names:
    r1 = requests.get(f"{base_url}{end_point_index_prices}?symbol={i}")
    r2 = requests.get(f"{base_url}{end_point_klines}?symbol={i}&interval={timeframe}&limit=1")
    coin_prices.append({'name': i, 'index_price': float(r1.json()['indexPrice']), 'highest_price': float(r2.json()[0][2]),
                        'lowest_price': float(r2.json()[0][3])})

while True:
    bot.send_message(chat_id, text=(to_buy_pr_change(coin_prices)))
    bot.send_message(chat_id, text=to_sell_pr_change(coin_prices))
    bot.send_message(chat_id, text=buy_signal_macd(coin_prices,base_url,end_point_klines,timeframe))
    print("Message is sended")
    time.sleep(sending_interval[timeframe])


