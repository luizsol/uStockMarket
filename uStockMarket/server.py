#!flask/bin/python
# -*- coding: utf-8 -*-
# from decimal import Decimal
from decimal import Decimal

from flask import Flask, request
from flask_restful import reqparse, Api, Resource

from u_stock_market import StockExchange, log

sx = StockExchange()
app = Flask(__name__)
api = Api(app)


# ====== System methods ======
# -Erases all the database
class CleanHistory(Resource):  # TODO test!
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


# -Get trader status
class TraderStatus(Resource):  # TODO test!
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


class SendOrder(Resource):  # TODO test!
    def put(self):
        args = send_order_parser.parse_args()
        if 'price' in args.keys():
            args['price'] = Decimal(args['price'])

        log.debug('/send_order (put): ' + str(args))
        return sx.register_trader(**args)

    def post(self):
        return self.put()


api.add_resource(SendOrder, '/send_order')

# -Assign equities to multiple traders


class EditPositions(Resource):  # TODO test!
    def put(self):
        args = request.get_json()
        log.debug('/edit_positions (put): ' + str(args))
        return sx.edit_positions(args)

    def post(self):
        return self.put()


api.add_resource(EditPositions, '/edit_positions')

# ====== OrderBook methods ======
# -List all securities


class ListTickers(Resource):
    def get(self):
        log.debug('/list_tickers (get): ')
        return sx.list_tickers()


api.add_resource(ListTickers, '/list_tickers')

# -Get security price history
# TODO

# -Get security order book
# TODO

# -Registers a new security
# TODO

if __name__ == '__main__':
    app.run(debug=True)
