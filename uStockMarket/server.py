#!flask/bin/python
# -*- coding: utf-8 -*-
# from decimal import Decimal

from flask import Flask
from flask_restful import reqparse, Api, Resource

from u_stock_market import StockExchange, log

sx = StockExchange()
app = Flask(__name__)
api = Api(app)


# Trader methods
# -Register a new trader
register_trader_parser = reqparse.RequestParser()
register_trader_parser.add_argument('name', type=str, help='The name of the '
                                    'new trader.')

register_trader_parser.add_argument('wallet', type=str, help='The initial'
                                    ' ammount of money of the trader.')

register_trader_parser.add_argument('portfolio', type=dict, help='A dict of '
                                    'dicts containing the security code '
                                    '(ticker) and its ammount, representing '
                                    'the trader\'s initial portfolio. Example'
                                    ': {"JBS02": 123, "LLC33": 223.23}')


class RegisterTrader(Resource):
    def get(self):
        return {'instruction': 'To register a new trader you should put or '
                               'post a json to the /register_trader URI '
                               'containing the following fields: name, wallet '
                               '(optional), portfolio (optional)'}, 400

    def put(self):
        args = register_trader_parser.parse_args()
        log.debug('/register_trader (put): ' + str(args))
        return sx.register_trader(**args)

    def post(self):
        return self.put()


api.add_resource(RegisterTrader, '/register_trader')

# -Get trader status
# TODO

# -Send order
# TODO

# -List trader orders
# TODO

# OrderBook methods
# -List all securities

class ListTickers(Resource):
    def put(self):
        return {'instruction': 'To register a new trader you should put or '
                               'post a json to the /register_trader URI '
                               'containing the following fields: name, wallet '
                               '(optional), portfolio (optional)'}, 400

    def get(self):
        log.debug('/list_tickers (get): ')
        return sx.list_tickers()

    def post(self):
        return self.put()


api.add_resource(ListTickers, '/list_tickers')

# -Get security price history
# TODO

# -Get security order book
# TODO

if __name__ == '__main__':
    app.run(debug=True)
