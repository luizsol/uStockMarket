#!flask/bin/python
# -*- coding: utf-8 -*-
"""A micro Stock Market Simulator.

This module implements the RESTful API of a Stock Exchange.

To see all the execution options, run:
    $ python server.py -h

Todo:
    * Add the Registers a new security view

.. _uStockMarket Project:
    https://github.com/luizsol/uStockMarket

"""
__author__ = 'Luiz Sol'
__license__ = 'MIT'
__version__ = '0.0.1'
__date__ = '2017-10-05'
__maintainer__ = 'Luiz Sol'
__email__ = 'luizedusol@gmail.com'
__status__ = 'Development'

import argparse
from decimal import Decimal

from flask import Flask, request
from flask_restful import reqparse, Api, Resource

from u_stock_market import StockExchange, log

# Adding the terminal options

parser = argparse.ArgumentParser(description='Runs the uStockMarket server.')
parser.add_argument('-c', metavar='--clean_start', nargs='?', default=True,
                    type=bool, help='true if the whole database should be '
                                    'erased before starting the server '
                                    '(default=true).')

parser.add_argument('-f', metavar='--config_file', nargs='?', default=None,
                    help='An yaml file containing the inititial market'
                         ' configuration.')

parser.add_argument('-d', metavar='--debug', nargs='?', default=True,
                    type=bool, help='true if the server should run on debug '
                                    'mode (default=true).')

args = parser.parse_args()

sx = StockExchange(config_file=args.f, clean_start=args.c, debug_mode=args.d)
sx.start()

app = Flask(__name__)
api = Api(app)


# ====== System methods ======
# -Erases all the database
class CleanHistory(Resource):
    def get(self):
        log.debug('/clean_history (get): ')
        return sx.clean_history()


api.add_resource(CleanHistory, '/clean_history')

# ====== Trader methods ======
# -Registers a new trader
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

# -List traders


class ListTraders(Resource):
    def get(self):
        log.debug('/list_traders (get): ')
        return sx.list_traders()


api.add_resource(ListTraders, '/list_traders')


# -Get trader status
class TraderStatus(Resource):
    def get(self, name):
        log.debug('/trader_status/%s (get): ' % (name))
        return sx.get_trader_status(name)


api.add_resource(TraderStatus, '/trader_status/<name>')

# -Send order
send_order_parser = reqparse.RequestParser()
send_order_parser.add_argument('trader', type=str, help='The name of the '
                               'trader.')

send_order_parser.add_argument('ticker', type=str, help='The security code '
                               '(ticker).')

send_order_parser.add_argument('side', type=str, help='"buy" for an Bid order '
                               'and "sell" for an Ask order.')

send_order_parser.add_argument('size', type=int, help='The order\'s size.')

send_order_parser.add_argument('price', type=str, help='The order\'s price.')

send_order_parser.add_argument('market_order', type=bool, help='Whether the '
                               'order should be a `at market price` '
                               '(optional)')


class SendOrder(Resource):
    def put(self):
        args = send_order_parser.parse_args()
        if args['price'] is not None:
            args['price'] = Decimal(args['price'])

        log.debug('/send_order (put/post): ' + str(args))
        return sx.send_order(**args)

    def post(self):
        return self.put()


api.add_resource(SendOrder, '/send_order')

# -Assign equities to multiple traders


class EditPositions(Resource):
    def put(self):
        args = request.get_json()
        log.debug('/edit_positions (put/post): ' + str(args))
        return sx.edit_positions(args)

    def post(self):
        return self.put()


api.add_resource(EditPositions, '/edit_positions')

# ====== OrderBook methods ======
# -Registers a new security

register_security_parser = reqparse.RequestParser()
register_security_parser.add_argument('ticker', type=str, help='The security '
                                                               'code. ')


class RegisterSecurity(Resource):  # FIXME not working ('ticker' recieves None)
    def put(self):
        args = register_security_parser.parse_args()
        log.debug('/register_security (put/post): ' + str(args))
        print(args)
        return sx.register_security(args['ticker'])

    def post(self):
        return self.put()


api.add_resource(RegisterSecurity, '/register_security')

# -List all securities


class ListTickers(Resource):
    def get(self):
        log.debug('/list_tickers (get): ')
        return sx.list_tickers()


api.add_resource(ListTickers, '/list_tickers')

# -Get security price history


class PriceHistory(Resource):
    def get(self, ticker):
        log.debug('/price_history/%s (get): ' % (ticker))
        return sx.get_price_history(ticker)


api.add_resource(PriceHistory, '/price_history/<ticker>')

# -Get security order book


class Book(Resource):
    def get(self, ticker):
        log.debug('/book/%s (get): ' % (ticker))
        return sx.get_book(ticker)


api.add_resource(Book, '/book/<ticker>')

if __name__ == '__main__':
    app.run(debug=args.d)
