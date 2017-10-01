#!/usr/bin/env python
# -*- coding: utf-8 -*-

from u_stock_market import *

sx = StockExchange()
print(OrderBook.objects[0])

print(Trader.objects)

carlos = sx.register_trader('Carlos')

emanuel = sx.register_trader('Emanuel')

tiago = sx.register_trader('Tiago')

print(Trader.objects)

# for trader in Trader.objects:
#     print(trader)

book = OrderBook.objects[0]

ticker = book.ticker

tiago.send_order(ticker, 'buy', size=300, price=3.24)

carlos.send_order(ticker, 'sell', size=300, price=3.24)

print(book)
