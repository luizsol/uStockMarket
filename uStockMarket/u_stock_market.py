#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
import logging

import numpy as np
from mongoengine import *
from mongoengine.connection import get_connection

DB_NAME = 'u_stock_market'

connect(DB_NAME)


class StockExchange():
    """docstring for StockExchange"""

    def __init__(self, clean_start=True, log_file=None, debug_mode=True):

        self._new_log(log_file=log_file)

        if clean_start:
            self.clean_history()
            # Create new order books

    def clean_history(self):
        connection = get_connection()
        connection.drop_database(DB_NAME)

    def _new_log(self, log_file=None):

        # Source: https://docs.python.org/2.3/lib/node304.html
        self.log = logging.getLogger('u_stock_market')
        if log_file is None:
            log_file = 'u_stock_market.log'

        hdlr = logging.FileHandler(log_file)
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        hdlr.setFormatter(formatter)
        self.log.addHandler(hdlr)
        self.log.setLevel(logging.DEBUG)


class ValueDatum(EmbeddedDocument):
    value = DecimalField(min_value=0.01, precision=2, required=True)
    timestamp = DateTimeField(required=True)


class OrderBook(Document):
    ticker = StringField(max_length=50, unique=True)
    bid_orders = ListField(ReferenceField('Order'))
    ask_orders = ListField(ReferenceField('Order'))
    price_history = ListField(EmbeddedDocumentField(ValueDatum))
    # _mutex = False

    @classmethod
    def post_save(cls, sender, document, **kwargs):
        # TODO
        pass

    def get_market_price(self):
        # TODO
        pass

    def get_price_history(self):
        # TODO
        pass


class Trader(Document):
    name = StringField(max_length=50, unique=True, required=True)

    wallet = DecimalField(default=int(np.random.chisquare(10)) * 1000,
                          min_value=0.00, precision=2, required=True)

    wallet_history = ListField(EmbeddedDocumentField('ValueDatum'))

    portfolio = ListField(ReferenceField('Position'),
                          default=[Position(order_book=book,
                                   shares=int(np.random.chisquare(10)) * 100)
                                   for book in OrderBook.objects])

    orders = ListField(ReferenceField('Order'))

    @classmethod
    def post_save(cls, sender, document, **kwargs):
        # TODO
        pass

    def send_order(self):
        # TODO
        pass

    def cancel_order(self):
        # TODO
        pass

    def update_wallet(self):
        # TODO
        pass

    def get_portfolio_value(self):
        # TODO
        pass


class Position(Document):
    trader = ReferenceField('Trader', required=True)
    order_book = ReferenceField('OrderBook', required=True)
    shares = IntField(default=0, required=True)


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
        # Were any of the orders cancelled or filled?
        if self.canceled or self.filled or order.canceled or order.filled:
            return False

        # Are both orders on the same book?
        if self.order_book != order.order_book:
            return False

        # Are both orders on oposite sides?
        if self.order_type == order.order_type:
            return False

        # Are both order prices compatible?
        if self.price != order.price and (not self.market_order) \
           and (not oder.market_order):
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
            return False

        # Can the buyer pay for the fill?
        if buyer.wallet < fill_ammout * price:
            # Canceling the order
            if self.trader == buyer:
                self.canceled = True
            else:
                order.canceled = True
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

                return False
        except Exception:
            return False

        self.current_size -= fill_ammout
        order.current_size -= fill_ammout

        # Creating the fill
        fill = Fill(order=self, seller=seller, buyer=buyer, size=fill_ammout,
                    price=price, time=datetime.now())

        fill.save()

        # Updating the orders
        self.fills += [fill]
        oder.fills += [fill]

        if self.current_size == 0:
            self.filled = True

        if order.current_size == 0:
            order.filled = True

        self.save()
        oder.save()

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

        return fill


class Fill(Document):
    order = ReferenceField('Order', required=True)
    seller = ReferenceField('Trader', required=True)
    buyer = ReferenceField('Trader', required=True)
    size = IntField(min_value=1, required=True)
    price = DecimalField(min_value=0.01, precision=2, required=True)
    time = DateTimeField(default=datetime.now(), required=True)
