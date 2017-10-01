#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
import logging
import random
import string

import numpy as np
from mongoengine import *
from mongoengine.connection import get_connection


DB_NAME = 'u_stock_market'
LOG_FILE = 'u_stock_market.log'


def _new_log(log_file=None):
    # Source: https://docs.python.org/2.3/lib/node304.html
    log = logging.getLogger('u_stock_market')
    if log_file is None:
        log_file = LOG_FILE

    hdlr = logging.FileHandler(log_file)
    formatter = logging.Formatter('[%(asctime)s][%(levelname)s] %(message)s')
    hdlr.setFormatter(formatter)
    log.addHandler(hdlr)
    log.setLevel(logging.DEBUG)
    return log


log = _new_log()

connect(DB_NAME)


class StockExchange():
    """docstring for StockExchange"""

    def __init__(self, clean_start=True, log_file=None, debug_mode=True,
                 tickers=None):
        log.info('Starting stock exchange')

        if clean_start:
            log.info('Cleaning all market history')

            self.clean_history()

            if tickers is None:
                log.info('Generating random tickers')
                for i in range(0, random.randint(1, 100)):
                    while self.register_ticker(self._random_ticker()) is None:
                        pass

            else:
                log.info('Generating tickers')
                for ticker in tickers:
                    self.register_ticker(ticker)

    def _random_ticker(self, num_letters=4):
        letters = ''.join(random.choices(string.ascii_uppercase, k=4))
        digits = ''.join(random.choices(string.digits, k=2))

        return letters + digits

    def clean_history(self):
        connection = get_connection()
        connection.drop_database(DB_NAME)

    def register_ticker(self, ticker):
        try:
            OrderBook.objects.get(ticker=ticker)
            return None
        except Exception:
            order_book = OrderBook(ticker=ticker)
            order_book.save()
            return order_book

    def register_trader(self, name, wallet=None, portfolio=None):
        log.info('Registering new trader')
        try:
            Trader.objects.get(name=name)
            log.info('Name %s already exists. Aborting trader registration',
                     name)
            return False
        except Exception:
            pass

        if wallet is None:
            wallet = int(np.random.chisquare(10)) * 1000

        trader = Trader(name=name, wallet=wallet).save()

        if portfolio is not None:
            trader.portfolio = portfolio
        else:
            trader.portfolio = []
            for book in OrderBook.objects:
                position = Position(
                    trader=trader, order_book=book,
                    shares=int(np.random.chisquare(10)) * 10000)

                trader.portfolio += [position.save()]

        trader.save()
        log.info('%s created!', repr(trader))
        return trader


class Fill(Document):
    order = ReferenceField('Order', required=True)
    seller = ReferenceField('Trader', required=True)
    buyer = ReferenceField('Trader', required=True)
    size = IntField(min_value=1, required=True)
    price = DecimalField(min_value=0.01, precision=2, required=True)
    time = DateTimeField(default=datetime.now(), required=True)

    def __repr__(self):
        return 'Fill(seller=%s, buyer=%s, size=%s, price=%s)' % \
            (self.seller.name, self.buyer.name, self.size, self.price)


class Position(Document):
    trader = ReferenceField('Trader', required=True)
    order_book = ReferenceField('OrderBook', required=True)
    shares = IntField(default=0, required=True)

    def __repr__(self):
        return 'Position(trader=%s, ticker=%s, shares=%s)' % \
            (self.trader.name, self.order_book.ticker, self.shares)


class ValueDatum(EmbeddedDocument):
    value = DecimalField(min_value=0.01, precision=2, required=True)
    time = DateTimeField(required=True)

    def __repr__(self):
        return '[' + str(time) + '] ' + str(value)


class Trader(Document):
    name = StringField(max_length=50, unique=True, required=True)

    wallet = DecimalField(default=0,
                          min_value=0.00, precision=2, required=True)

    wallet_history = ListField(EmbeddedDocumentField('ValueDatum'))

    portfolio = ListField(ReferenceField('Position'))

    orders = ListField(ReferenceField('Order'))

    @classmethod
    def post_save(self, sender, document, **kwargs):
        if self.wallet != self.wallet_history.objects.order_by('-time').value:
            self.wallet_history += [ValueDatum(time=datetime.now(),
                                               value=self.wallet)]

    def send_order(self, ticker, side, size, price=None,
                   market_order=False):
        log.info('Sending order:\nTrader: %s, Ticker: %s, Side: %s, '
                 'Size: %s, Price: %s, Market_order: %s', self.name, ticker,
                 side, size, price, market_order)
        try:
            book = OrderBook.objects.get(ticker=ticker)
        except Exception:
            log.warning('Order %s rejected!', repr(order))
            return None

        if side == 'buy':
            order_type = 'Bid'
        else:
            order_type = 'Ask'

        order = Order(trader=self,
                      order_book=book,
                      original_size=size,
                      current_size=size,
                      price=price,
                      market_order=market_order,
                      order_type=order_type)

        order.save()

        log.info('Order sent! (%s)', repr(order))
        book.try_match()

        return order

    def update_wallet(self, value):
        self.wallet += value
        self.save()

    def get_portfolio_value(self):
        t_value = Decimal('0.00')

        for position in self.portfolio:
            t_value += position.shares * position.order_book.get_market_price()

        return t_value

    def __repr__(self):
        return 'Trader(name=%s, wallet=%s)' % (str(self.name),
                                               str(self.wallet))

    def __str__(self):
        return 'Trader:\n\tName: %s\n\tWallet: %s\n\tPortfolio: \n\t\t%s' % \
               (self.name, self.wallet,
                '\n\t\t'.join([repr(position) for position in self.portfolio]))


class Order(Document):
    """docstring for Order"""
    trader = ReferenceField('Trader', required=True)
    order_book = ReferenceField('OrderBook', required=True)
    original_size = IntField(min_value=1, required=True)
    current_size = IntField(required=True)
    time = DateTimeField(default=datetime.now(), required=True)
    price = DecimalField(min_value=0.01, precision=2, required=True)
    market_order = BooleanField(default=False, required=True)
    canceled = BooleanField(default=False, required=True)
    filled = BooleanField(default=False, required=True)
    fills = ListField(ReferenceField('Fill'))
    order_type = StringField(choices=('Bid', 'Ask'), required=True)

    def match(self, order, market_price=None):
        log.info('Matching orders %s and %s.', repr(self), repr(order))
        # Were any of the orders cancelled or filled?
        if self.canceled or self.filled or order.canceled or order.filled:
            log.info('Orders %s and %s not matched (one of them is'
                     ' canceled).', repr(self), repr(order))
            return False

        # Are both orders on the same book?
        if self.order_book != order.order_book:
            log.info('Orders %s and %s not matched (they are in separate'
                     ' books).', repr(self), repr(order))
            return False

        # Are both orders on oposite sides?
        if self.order_type == order.order_type:
            log.info('Orders %s and %s not matched (they have the same '
                     ' order type).', repr(self), repr(order))
            return False

        # Are both order prices compatible?
        if self.price != order.price and (not self.market_order) \
           and (not oder.market_order):
            log.info('Orders %s and %s not matched (they have different '
                     ' prices).', repr(self), repr(order))
            return False

        fill_ammout = min(self.current_size, order.current_size)

        if self.order_type == 'Ask':
            buyer = order.trader
            seller = self.trader
        else:
            seller = order.trader
            buyer = self.trader

        if not self.market_order:
            price = self.price
        elif not order.market_order:
            price = order.price
        elif market_price is not None:
            price = market_price
        else:
            # Can't determine the price of the fill
            log.info('Orders %s and %s not matched (can\'t determine the '
                     ' price of the fill).', repr(self), repr(order))
            return False

        # Can the buyer pay for the fill?
        if buyer.wallet < fill_ammout * price:
            # Canceling the order
            if self.trader == buyer:
                self.canceled = True
            else:
                order.canceled = True

            log.info('Orders %s and %s not matched (the buyer does\'t have '
                     ' enough money).', repr(self), repr(order))
            return False

        # Does the seller has the stocks?
        try:
            seller_position = Position.objects.get(trader=seller,
                                                   order_book=self.order_book)
            if seller_position.shares < fill_ammout:
                # Canceling the order
                if self.trader == seller:
                    self.canceled = True
                else:
                    order.canceled = True

                log.info('Orders %s and %s not matched (the seller doesn\'t'
                         ' have the securities).', repr(self), repr(order))

                return False
        except Exception:
            log.info('Orders %s and %s not matched (the seller doesn\'t'
                     ' have the securities).', repr(self), repr(order))
            return False

        self.current_size -= fill_ammout
        order.current_size -= fill_ammout

        # Creating the fill
        fill = Fill(order=self, seller=seller, buyer=buyer, size=fill_ammout,
                    price=price, time=datetime.now())

        fill.save()

        # Updating the orders
        self.fills += [fill]
        order.fills += [fill]

        if self.current_size == 0:
            self.filled = True

        if order.current_size == 0:
            order.filled = True

        self.save()
        order.save()

        # Updating the traders positions
        seller_position.shares -= fill_ammout
        try:
            buyer_position = Position.objects.get(trader=buyer,
                                                  order_book=self.order_book)
        except Exception:
            buyer_position = Position(trader=buyer, order_book=self.order_book)

        buyer_position.shares += fill_ammout

        seller_position.save()
        buyer_position.save()

        log.info('Orders %s and %s matched (fill: %s).', repr(self),
                 repr(order), repr(fill))

        log.info('PRICE UPDATE: %s %s.', self.order_book.ticker, fill.price)

        return fill

    def __repr__(self):
        return 'Order(trader=%s, ticker=%s, current_size=%s, price=%s, ' \
               'market_order=%s, order_type=%s)' % \
               (self.trader.name, self.order_book.ticker, self.current_size,
                self.price, self.market_order, self.order_type)


class OrderBook(Document):
    ticker = StringField(max_length=50, unique=True)
    price_history = ListField(EmbeddedDocumentField(ValueDatum))
    # _mutex = False

    def try_match(self):
        log.info('Trying to mach orders on the book %s.', repr(self))
        top_bid = self.get_top_bid()
        top_ask = self.get_top_ask()

        print(top_bid)
        print(top_ask)

        if top_bid is not None and top_ask is not None:
            fill = top_bid.match(top_ask, market_price=self.get_market_price())

            if fill:
                datum = ValueDatum(time=fill.time, value=fill.price)
                self.price_history += [datum]
                self.save()
                self.try_match()
        else:
            log.info('Not enough orders to try a match on the book %s.',
                     repr(self))

    def get_top_bid(self, force_price=False):
        log.debug('Searchig for top bid on the book %s.', repr(self))

        log.debug('Searchig for top market price bid on the book %s.',
                  repr(self))
        try:
            if force_price:
                raise Exception

            return Order.objects(
                order_book=self, order_type='Bid', canceled=False,
                filled=False, market_order=True).order_by('-time',
                                                          '-current_size')[0]

        except Exception:
            pass

        log.debug('Searchig for top bid with price on the book %s.',
                  repr(self))

        try:
            return Order.objects(
                order_book=self, order_type='Bid', canceled=False,
                filled=False).order_by('-price', '-time', '-current_size')[0]

        except Exception:
            log.debug('Couldn\'t fid top bid on the book %s.', repr(self))
            return None

    def get_top_ask(self, force_price=False):
        try:
            if force_price:
                raise Exception

            return Order.objects(
                order_book=self, order_type='Ask', canceled=False,
                filled=False, market_order=True).order_by('-time',
                                                          '-current_size')[0]

        except Exception:
            try:
                return Order.objects(
                    order_book=self, order_type='Ask', canceled=False,
                    filled=False).order_by('price', '-time',
                                           '-current_size')[0]

            except Exception:
                return None

    def get_market_price(self):

        if len(self.price_history) > 0:
            return self.price_history[-1].value
        else:
            return None

    def __repr__(self):
        return 'OrderBook(ticker=' + self.ticker + ')'

    def __str__(self):
        result = 'OrderBook:\n'
        result += '\tTicker: ' + self.ticker + '\n'
        result += '\tMarket price: ' + str(self.get_market_price()) + '\n'

        total_bids = 0
        try:
            total_bids = len(Order.objects(order_type='Bid', canceled=False,
                                           filled=False))
        except Exception:
            pass

        result += '\tActive Bids: ' + str(total_bids)

        total_aks = 0
        try:
            total_aks = len(Order.objects(order_type='Ask', canceled=False,
                                          filled=False))
        except Exception:
            pass

        result += '\tActive Asks: ' + str(total_aks) + '\n'
        return result
