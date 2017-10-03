#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A micro Stock Market Simulator.

This module implements the internal's of a Stock Exchange.

The main interaction with this module should be made through the StockExchange
class and it's methods since most of the logic is inside it.

Avoid writing data to the u_stock_market database without the use of the
StockExchange methods at all costs as to avoid data inconsistencies.

Attributes:
    DB_NAME (str): the name of the mongodb database to be used by the
         application
    LOG_FILE (str): the default name of the log file
    log (logging): the module's logging object

Todo:
    * Implement the user defined log output on the StockExchange constructor
    * Implement the user defined optional log level
    * Change the `except Exception:` statements to catch only database related
        exceptions
    * Make the StockExchange methods return standarized dicts instead of
        objects
    * Improve the validation on the creation methods of the StockExchange class
    * Test thread safety
    * Implement the trader's portfolio history
    * Implement the wallet history updating
    * Use module constants to represent Bid and Ask orders
    * Improve logging consistency and depth
    * Add market depth info to the OrderBook.to_dict() method

Future features:
    * Implement short position support


.. _uStockMarket Project:
    https://github.com/luizsol/uStockMarket

"""
__author__ = 'Luiz Sol'
__license__ = 'GPL'
__version__ = '0.0.1'
__date__ = '2017-10-02'
__maintainer__ = 'Luiz Sol'
__email__ = 'luizedusol@gmail.com'
__status__ = 'Development'

from datetime import datetime
from decimal import Decimal
import logging
import random
import string

import numpy as np
from mongoengine import *
from mongoengine.connection import get_connection


DB_NAME = 'u_stock_market'
LOG_FILE = 'u_stock_market.log'


def _new_log(log_file=None):
    """Generates and prepares a logging object.

    Keyword Args:
        log_file (str, default=None): The file path of the log file.

    Returns:
        logging: A pre configured logging object.

    .. _Source:
        https://docs.python.org/2.3/lib/node304.html

    """
    log = logging.getLogger('u_stock_market')
    if log_file is None:
        log_file = LOG_FILE

    hdlr = logging.FileHandler(log_file)
    formatter = logging.Formatter('[%(asctime)s][%(levelname)s] %(message)s')
    hdlr.setFormatter(formatter)
    log.addHandler(hdlr)
    log.setLevel(logging.DEBUG)
    return log


def bad_request(message):
    """(dict, status) Returns a default error dict with a specified message."""
    return {'success': False, 'message': message}, 400


def good_request(data):
    """(dict, status) Returns a default success dict with a specified data."""
    return {'success': True, 'data': data}, 200


def dict_to_porfolio(trader, portfolio):
    """Generates a trader portfolio based on a dict.

    The dict should be formatted as ticker: amount

    Examples:
        {"JBS02": 123, "LLC33": 223.23}

    Args:
        trader (Trader): The trader of the portfolio being created.
        porfolio (dict): The dict to be converted on a portfolio.

    Returns:
        False if one of the dict ticker is not registered in any OrderBook, the
        list of positions representing the trader's portfolio otherwise.

    """
    result = []
    for ticker, shares in portfolio.items():
        try:
            book = OrderBook.objects.get(ticker=ticker)
            result += [Position(trader=trader, order_book=book, shares=shares)]
        except Exception:
            return False
    return result


log = _new_log()

connect(DB_NAME)


class StockExchange():
    """The Stock Exchange backend.

    This class is the interface through wich all users should interact with the
    System.

    In this class methods the trader can perform the most common interactions
    of regular stock exchanges, such as sending orders, fetching his portfolio
    position etc.

    Besides that and maintaining the data consistency, in order to make the
    simulation the most realistic possible, these class methods remove from the
    query result all data that wouldn't be available on a real situation to the
    trader that is sending the request.

    The direct use of the other classes in this module is only advised to the
    users that want to have a more complete market view.

    """

    def __init__(self, clean_start=True, log_file=None, debug_mode=True,
                 tickers=None):
        """The class constructor.

        Keyword Args:
            clean_start (bool, default=True): Whether the database should be
                erased before running the system.
            log_file (str, default=None): The file name into which the log must
                be saved. If `None` the log will be saved on the default file.
            debug_mode (bool, default=True): If True the log level will be set
                to logging.DEBUG. If false, the log level will me set to
                logging.INFO.

        """
        log.info('Starting stock exchange')

        if clean_start:
            log.info('Cleaning all market history')

            self.clean_history()

            if tickers is None:
                log.info('Generating random tickers')
                for i in range(0, random.randint(1, 100)):
                    while self.register_security(self._random_ticker()) \
                            is None:
                        pass

            else:
                log.info('Generating tickers')
                for ticker in tickers:
                    self.register_security(ticker)

    def _random_ticker(self, num_letters=4, num_digits=2):
        """Generates a random security code (ticker).

        The generated ticker will have the form <letters><numbers>.

        Examples:
            AAKL32, BSUE34, NDUR09

        Keyword Args:
            num_letters (int, default=4): The number of letters to be used on
                the ticker.
            num_digits (int, default=2): The number of digits to be used on
                the ticker.

        Returns:
            str: the random ticker.

        """
        letters = ''.join(random.choices(string.ascii_uppercase,
                                         k=num_letters))

        digits = ''.join(random.choices(string.digits, k=num_digits))

        return letters + digits

    def clean_history(self):
        """Erases all the module's database"""
        connection = get_connection()
        connection.drop_database(DB_NAME)
        return good_request('The database was erased.')

    def register_security(self, ticker):
        """Creates a new OrderBook for a security.

        This is the method through wich a new security must be created.

        Args:
            ticker (str): The security code (ticker).

        Returns:
            None if a security with the same ticker already exists, the
            security's OrderBook otherwise.

        """
        try:
            OrderBook.objects.get(ticker=ticker)
            return None
        except Exception:
            order_book = OrderBook(ticker=ticker)
            order_book.save()
            return order_book

    def register_trader(self, name, wallet=None, portfolio=None):
        """Registers a new trader.

        This is the method through wich a new trader must be created.

        Args:
            name (str): The trader's name.

        Keyword Args:
            wallet (Decimal, default=None): The inital amount of money of the
                trader. If set to None a random value (with a Chi Squared
                distribution) will be assigned to the trader's initial wallet.
            portfolio(dict, default=None): The initial porfolio of
                the trader. If set to None a random porfolio of all available
                securities (with a Chi Squared distribution) will be assigned
                to the trader. Example of initial portfolio representation:
                {"JBS02": 123, "LLC33": 223.23}

        Returns:
            None if a trader with the same name already exists, the Trader
            object otherwise.

        """
        log.info('Registering new trader')
        try:
            Trader.objects.get(name=name)
            log.info('Name %s already exists. Aborting trader registration',
                     name)
            return bad_request('The %s trader already exists.' % (name))
        except Exception:
            pass

        if wallet is None:
            wallet = int(np.random.chisquare(10)) * 1000

        trader = Trader(name=name, wallet=wallet).save()

        if portfolio is not None:
            portfolio = dict_to_porfolio(trader, portfolio)
            if portfolio:
                for position in portfolio:
                    position.save()

                trader.portfolio = portfolio
            else:
                trader.delete()
                return bad_request('Invalid portfolio.')
        else:
            trader.portfolio = []
            for book in OrderBook.objects:
                position = Position(
                    trader=trader, order_book=book,
                    shares=int(np.random.chisquare(10)) * 10000)

                trader.portfolio += [position.save()]

        trader.save()
        log.info('%s created!', repr(trader))
        return good_request(trader.to_dict())

    def list_tickers(self):
        return good_request({'tickers': [book.ticker for book in
                                         OrderBook.objects]})

    def get_trader_status(self, name):  # TODO test!
        try:
            return good_request(Trader.objects.get(name=name).to_dict())
        except Exception:
            return bad_request('The trader doesn\'t exist.')

    def send_order(self, trader, ticker, side, size, price=None,
                   market_order=False):  # TODO test!
        try:
            trader = Trader.objects.get(name=trader)
        except Exception:
            return bad_request('The trader doesn\'t exist.')

        result = trader.send_order(ticker, side, size, price=price,
                                   market_order=market_order)

        if result is not None:
            return good_request(result.to_dict())

        return bad_request('The order was refused.')

    def edit_positions(self, positions):  # TODO test!
        """Edits the portfolio positions of multiple traders.

        Example:
            {'John Doe': {'TTLB03': 334, 'JJBE32': 700, 'KKTB38': 1020},
             'Bruce Wayne': {'TTLB03': 339823, 'LLCR33': 9000000}}

        Args:
            position (dict): A dict containing all the trader positions to be
                edited.

        Returns:
            None if a trader with the same name already exists, the Trader
            object otherwise.

        """
        if positions is None or not isinstance(positions, dict):
            return bad_request('Invalid request.')

        # Checking whether all keys on the dict are registered traders
        try:
            for trader in positions.keys():
                Trader.objects.get(name=trader)
                for ticker in positions[trader].keys():
                    OrderBook.objects.get(ticker=ticker)
        except Exception:
            return bad_request('One of the traders or ticker is not '
                               'registered.')

        for trader in positions.keys():
                Trader.objects.get(name=trader).update_portfolio(
                    positions[trader])

        return good_request('Positions updated successfully.')


class Fill(Document):
    """Represents an order fill via the Mongoengine ORM.

    A fill is the action of completing or satisfying an order for a security or
    commodity. It is the basic act in transacting stocks, bonds or any other
    type of security.

    An order may take many fills to be satisfied.

    Example:
        If a trader places a buy order for a stock at $50 and a seller agrees
        to the price, the sale has been made and the order has been filled.
        The $50 price is the execution price, which also makes it the fill
        price - it is the price that allows the transaction to be completed.

    Attributes:
        order (Order): The order that this fill totally or partially satisfied.
        seller (Trader): The trader that sold it's securities and generated
            this fill.
        buyer (Trader): The trader that bought the securities and generated
            this fill.
        size (int): The size of the fill.
        price (Decimal): The price of the fill.
        time (datetime): The time in which the fill was created.

    .. _Fill definition on Investopedia:
        http://www.investopedia.com/terms/f/fill.asp

    """
    order = ReferenceField('Order', required=True)
    seller = ReferenceField('Trader', required=True)
    buyer = ReferenceField('Trader', required=True)
    size = IntField(min_value=1, required=True)
    price = DecimalField(min_value=0.01, precision=2, required=True)
    time = DateTimeField(default=datetime.now(), required=True)

    def to_dict(self):
        return {
            'order': str(self.order.id),
            'seller': str(self.seller.name),
            'buyer': str(self.buyer.name),
            'size': str(self.size),
            'price': str(self.price),
            'time': str(self.time)}

    def __repr__(self):
        return 'Fill(seller=%s, buyer=%s, size=%s, price=%s)' % \
            (self.seller.name, self.buyer.name, self.size, self.price)


class Position(Document):
    """Represents a trader position via the Mongoengine ORM.

    A position is the amount of a security  that is owned (a long position) or
    borrowed and then sold (a short position, not supported yet) by a trader.

    Attributes:
        trader (Trader): The trader who owns the position.
        order_book (OrderBook): The order book of the security which this
            position represents.
        shares (int): The size of the position.

    .. _Position definition on Investopedia:
        http://www.investopedia.com/terms/p/position.asp

    """
    trader = ReferenceField('Trader', required=True)
    order_book = ReferenceField('OrderBook', required=True)
    shares = IntField(default=0, required=True)

    @property
    def value(self):
        """(Decimal) The position value virtual attribute getter."""
        mkt_p = self.order_book.get_market_price()
        if mkt_p is not None:
            return Decimal(self.shares * mkt_p)

        return Decimal('0.00')

    def __repr__(self):
        return 'Position(trader=%s, ticker=%s, shares=%s)' % \
            (self.trader.name, self.order_book.ticker, self.shares)

    def to_dict(self):
        return {
            'trader': str(self.trader.name),
            'ticker': str(self.order_book.ticker),
            'shares': str(self.shares),
            'value': str(self.value)}


class ValueDatum(EmbeddedDocument):
    """Represents a generic time series Decimal datum via the Mongoengine ORM.

    Attributes:
        value (Decimal): The datum value.
        time (datetime): The datum time.

    """
    value = DecimalField(min_value=0.01, precision=2, required=True)
    time = DateTimeField(required=True)

    def __repr__(self):
        return '[' + str(time) + '] ' + str(value)

    def to_dict(self):
        return {
            'value': str(self.value),
            'time': str(self.time)}


class Trader(Document):
    """Represents a trader via the Mongoengine ORM.

    A trader is an individual who engages in the buying and selling of
    financial assets in any financial market, either for himself or on behalf
    of another person or institution.

    Attributes:
        name (str): The name of the trader.
        wallet (Decimal): The ammout of money that the trader has.
        wallet_history (list(ValueDatum)): The history of the trader's wallet.
        portfolio (Portfolio): The trader's portfolio.
        orders (list(Order)): A list with all the orders sent by the trader.

    .. _Trader definition on Investopedia:
        http://www.investopedia.com/terms/t/trader.asp

    """
    name = StringField(max_length=50, unique=True, required=True)

    wallet = DecimalField(default=0,
                          min_value=0.00, precision=2, required=True)

    wallet_history = ListField(EmbeddedDocumentField('ValueDatum'))

    portfolio = ListField(ReferenceField('Position'))

    orders = ListField(ReferenceField('Order'))

    def update_wallet_history(self):
        """Updates the wallet_history time series."""
        if self.wallet != self.wallet_history.objects.order_by('-time').value:
            self.wallet_history += [ValueDatum(time=datetime.now(),
                                               value=self.wallet)]
            self.save()

    def send_order(self, ticker, side, size, price=None,
                   market_order=False):
        """Sends an order on behalf of the trader.

        Args:
            ticker (str): The security code (ticker).
            side (str): If 'buy' will send an Bid order, if 'sell' will send an
                Ask order.
            size (int): The size of the order.

        Keyword Args:
            price (Decimal, default=None): The price of the order. May be left
                as None just in the case of a `at market price` order.
            market_order (bool, default=False): Whether the order is a `at
                market price` order.

        Returns:
            None if the security doesn't exist, the sent order otherwise.

        """
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

        self.orders += [order]
        self.save()

        log.info('Order sent! (%s)', repr(order))
        book.try_match()

        return order

    def update_wallet(self, delta):
        """Adds a value to the trader's wallet.

        Args:
            delta (Decimal): The ammout of money to be added to the trader's
                wallet.

        """
        self.wallet += delta
        self.save()
        self.update_wallet_history()

    def get_portfolio_value(self):
        """(Decimal) Gets the current value of the trader's portfolio."""
        t_value = Decimal('0.00')

        for position in self.portfolio:
            t_value += Decimal(position.shares) * \
                position.order_book.get_market_price()

        return t_value

    def to_dict(self):
        return {
            'name': self.name,
            'wallet': str(self.wallet),
            'wallet_history': [datum.to_dict() for datum in
                               self.wallet_history],
            'portfolio': [position.to_dict() for position in self.portfolio],
            'portfolio_value': str(self.get_portfolio_value()),
            'orders': [order.to_dict() for order in self.orders]}

    def update_portfolio(self, new_positions):
        for key, value in new_positions.items():
            book = OrderBook.objects.get(ticker=key)
            try:
                position = Position.objects.get(order_book=book, trader=self)
                position.shares = int(value)
            except Exception:
                position = Position(order_book=book, trader=self,
                                    shares=int(value))

            position.save()

            if position not in self.portfolio:
                self.portfolio += [position]

            self.save()

    def __repr__(self):
        return 'Trader(name=%s, wallet=%s)' % (str(self.name),
                                               str(self.wallet))

    def __str__(self):
        return 'Trader:\n\tName: %s\n\tWallet: %s\n\tPortfolio: \n\t\t%s' % \
               (self.name, self.wallet,
                '\n\t\t'.join([repr(position) for position in self.portfolio]))


class Order(Document):
    """Represents an order via the Mongoengine ORM.

    An order is a trader's instructions to purchase or sell a security.

    Attributes:
        trader (Trader): The trader who sent the order.
        order_book (OrderBook): The order book into which this order was
            placed.
        original_size (int): The size of the order at it's creation.
        current_size (int): The current size of the order, which is defined by
            the order's original size minus the total size of all this order's
            partial fills.
        time (datetime): The time in which the order was sent.
        price (Decimal): The order's price.
        market_order (bool): Whether the order should be executed at the
            current market price or at a fixed price.
        canceled (bool): Whether an order was cancelled.
        filled (bool): Whether an order was already fully filled.
        fills (list(Fill)): The list of fills associated with this order.
        order_type (str): Whether this order is a Bid (buy) or an Ask (sell).


    .. _Order definition on Investopedia:
        http://www.investopedia.com/terms/o/order.asp

    """
    trader = ReferenceField('Trader', required=True)
    order_book = ReferenceField('OrderBook', required=True)
    original_size = IntField(min_value=1, required=True)
    current_size = IntField(required=True)
    time = DateTimeField(default=datetime.now(), required=True)
    price = DecimalField(min_value=0.01, precision=2)
    market_order = BooleanField(default=False, required=True)
    canceled = BooleanField(default=False, required=True)
    filled = BooleanField(default=False, required=True)
    fills = ListField(ReferenceField('Fill'))
    order_type = StringField(choices=('Bid', 'Ask'), required=True)

    def match(self, order, market_price=None):
        """Tries to match two orders with each other.

        Every time the order book recieve a new order it will try to match the
        top Bid order with the top Ask order through this method.

        The matching of two orders demands that:
            * Both orders are on the same order book.
            * None of them were cancelled or filled.
            * Both order are on oposite sides (one is an Ask and the other is a
                Bid).
            * Both orders have the same price or at least one of them is an `at
                market price` order.
            * The buyier can pay for the transaction.
            * The seller has the securities.

        If any of the above conditions is not met the matching will fail.

        Args:
            order (Order): the order with wich this order will attempt a match.

        Keyword Args:
            market_price (Decimal, default=None): If both orders are `at market
                price` orders this method will use this parameter as the fill
                price.

        Returns:
            False if it isn't possible to match both orders, the generated fill
            object otherwise.

        """
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

    def to_dict(self):
        return {
            'trader': str(self.trader.name),
            'ticker': str(self.order_book.ticker),
            'original_size': str(self.original_size),
            'current_size': str(self.current_size),
            'time': str(self.time),
            'price': str(self.price),
            'market_order': str(self.market_order),
            'canceled': str(self.canceled),
            'filled': str(self.filled),
            'fills': [fill.to_dict() for fill in self.fills],
            'order_type': str(self.order_type)}

    def __repr__(self):
        return 'Order(trader=%s, ticker=%s, current_size=%s, price=%s, ' \
               'market_order=%s, order_type=%s)' % \
               (self.trader.name, self.order_book.ticker, self.current_size,
                self.price, self.market_order, self.order_type)


class OrderBook(Document):
    """Represents an order book via the Mongoengine ORM.

    An order book is an electronic list of buy and sell orders for a specific
    security or financial instrument, organized by price level. The order book
    lists the number of shares being bid or offered at each price point, or
    market depth. It also identifies the market participants behind the buy and
    sell orders. The order book is dynamic and constantly updated in real time
    throughout the day.

    Attributes:
        ticker (str): The security symbol.
        price_history (list(ValueDatum)): The price time series of the security
            being traded on this order book.


    .. _Order book definition on Investopedia:
        http://www.investopedia.com/terms/o/order-book.asp

    """
    ticker = StringField(max_length=50, unique=True)
    price_history = ListField(EmbeddedDocumentField(ValueDatum))

    def try_match(self):
        """Tries to match the two top Ask and Bid orders.

        This method should be executed every time a new order is placed on this
        order book.

        Note:
            In the future, this method will be a callback of the save() method.

        """
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
        """Retrieves the top Bid order.

        The top Bid order is determined lexicographically on the following
        order:
            * Active (neither cancelled nor filled) order
            * `At market value` order
            * Highest price order
            * First order

        Keyword Args:
            force_price (bool, defautl=False): If True, the order sorting
                algorithm will discard all `at market price` orders.

        Returns:
            None if no valid Bid order was found, the top Bid order otherwise.

        """
        log.debug('Searchig for top bid on the book %s.', repr(self))

        log.debug('Searchig for top market price bid on the book %s.',
                  repr(self))
        try:
            if force_price:
                raise Exception

            return Order.objects(
                order_book=self, order_type='Bid', canceled=False,
                filled=False, market_order=True).order_by('time',
                                                          '-current_size')[0]

        except Exception:
            pass

        log.debug('Searchig for top bid with price on the book %s.',
                  repr(self))

        try:
            return Order.objects(
                order_book=self, order_type='Bid', canceled=False,
                filled=False).order_by('-price', 'time', '-current_size')[0]

        except Exception:
            log.debug('Couldn\'t fid top bid on the book %s.', repr(self))
            return None

    def get_top_ask(self, force_price=False):
        """Retrieves the top Ask order.

        The top Aks order is determined lexicographically on the following
        order:
            * Active (neither cancelled nor filled) order
            * `At market value` order
            * Lowest price order
            * First order

        Keyword Args:
            force_price (bool, defautl=False): If True, the order sorting
                algorithm will discard all `at market price` orders.

        Returns:
            None if no valid Bid order was found, the top Ask order otherwise.

        """
        try:
            if force_price:
                raise Exception

            return Order.objects(
                order_book=self, order_type='Ask', canceled=False,
                filled=False, market_order=True).order_by('time',
                                                          '-current_size')[0]

        except Exception:
            try:
                return Order.objects(
                    order_book=self, order_type='Ask', canceled=False,
                    filled=False).order_by('price', 'time',
                                           '-current_size')[0]

            except Exception:
                return None

    def get_market_price(self):
        """Determines the current market price.

        The current market price is here defined as the price of the last fill
        generated on this order book.

        Returns:
            None if no fill was yet generated, the current maket price
            (Decimal) otherwise.

        """
        if len(self.price_history) > 0:
            return self.price_history[-1].value
        else:
            return Decimal('0.00')

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

    def to_dict(self):
        # TODO add market depth info
        return{
            'ticker': self.ticker,
            'price_history': [datum.to_dict() for datum in self.price_history]}
