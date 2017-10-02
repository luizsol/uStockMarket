#!flask/bin/python
# -*- coding: utf-8 -*-

from flask import Flask

from u_stock_market import StockExchange

app = Flask(__name__)
sx = StockExchange()


@app.route('/')
def index():
    return "Hello, World!"


if __name__ == '__main__':
    app.run(debug=True)
