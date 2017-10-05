#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A micro Stock Market Simulator trader robot.

This module implements a trading robot that trades on the u_stock_market
system via the RESTful API.

Todo:
    * Implement more strategies
    * Implement data visualization
    * Implement more data retrieving options via DataFrame

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

from decimal import Decimal
import json
import random
import string
import threading
import time
import urllib.request

import pandas as pd


class RobotTrader(threading.Thread):
    """The robot trader class.

    This class implements all the available interactions with the Stock Market
    via it's methods. It also implements some very simple trading strategies.

    The main purpose of this class is to populate the stock market with
    multiple players.

    It inherits from threading.Thread so it can execute it's strategy
    asynchronously.

    """
    # Random strategy with order prices (see _random_strategy())
    RANDOM_STR = 0
    # Random strategy with order `at market price` (see
    # _random_strategy_market())
    RANDOM_MKT_STR = 1

    def __init__(self, name=None, strategy=0, wallet=None,
                 portfolio=None, server_addr=None):
        """The class constructor.

        Keyword Args:
            name (str, default=None): The name of the trading robot. If left to
                None a random name will be assigned.
            strategy (int, default=RobotTrader.RANDOM_STR): The strategy to be
                used by the trading robot.
            wallet (Decimal, default=None): The initial robot wallet. If left
                to None a random wallet value will be assigned.
            portfolio (dict, default=None): The initial robot portfolio. If
                left to None a random portfolio will be assigned.
            server_addr (str, default=None): The URL of the Stock Exchange. If
                left to None will use the Flask's default local address and
                port.

        """
        threading.Thread.__init__(self)

        if strategy == self.RANDOM_STR:
            self.strategy_fun = self._random_strategy
        elif strategy == self.RANDOM_MKT_STR:
            self.strategy_fun = self._random_strategy_market
        else:
            raise Exception('No strategy assigned')

        # super(threading.Thread, self).__init__()
        self.daemon = True

        self.strategy = strategy
        self.server_addr = 'http://127.0.0.1:5000/' if server_addr is None \
            else server_addr

        self.name = self._random_name() if name is None else name

        self.register(wallet=wallet, portfolio=portfolio)

    def register(self, wallet=None, portfolio=None):
        """Registers the trading robot on the Stock Exchange.

        Keyword Args:
            wallet (Decimal, default=None): The initial robot wallet. If left
                to None a random wallet value will be assigned.
            portfolio (dict, default=None): The initial robot portfolio. If
                left to None a random portfolio will be assigned.

        """
        trader = {'name': self.name}
        if wallet is not None:
            trader['wallet'] = wallet

        if portfolio is not None:
            trader['portfolio'] = portfolio

        result = self._post('register_trader', trader)
        return self._parse_response(result, 'Error while registering trading '
                                            'robot')

    def get_current_status(self):
        """Retrieves all information about the trading robot."""
        result = self._get('trader_status/' + self.name)
        return self._parse_response(result, 'Error while retrieving %s trader'
                                            ' data.' % (self.name))

    def update_status(self):
        """Retrieves and updates all information about the trading robot."""
        result = self.get_current_status()
        self.wallet = Decimal(result['wallet'])
        self.portfolio = result['portfolio']
        self.wallet_history = result['wallet_history']

    def send_order(self, ticker, side, size, price=None, market_order=False):
        """Sends an order.

        Args:
            ticker (str): The security code.
            side (str): If 'buy' will send an Bid order, if 'sell' will send an
                Ask order.
            size (int): The size of the order.

        Keyword Args:
            price (Decimal, default=None): The price of the order. May be left
                as None just in the case of a `at market price` order.
            market_order (bool, default=False): Whether the order is a `at
                market price` order.

        """
        result = self._post('send_order', {'trader': self.name,
                                           'ticker': ticker,
                                           'side': side,
                                           'size': size,
                                           'price': price,
                                           'market_order': market_order})

        return self._parse_response(result, 'Error while sending order '
                                            '(trader=%s)' % (self.name))

    def get_all_tickers(self):
        """(list) Retrieves all the registered security codes."""
        result = self._get('list_tickers')
        return self._parse_response(result,
                                    'Error while listing tickers (trader=%s)' %
                                    (self.name))['tickers']

    def get_book(self, ticker):
        """Retrieves the order book data of a security.

        Args:
            ticker (str): The security code.

        Returns:
            dict: A dict containing the OrderBook information.

        """
        result = self._get('book/' + ticker)
        return self._parse_response(result, 'Error while retrieving book '
                                            '(trader=%s, ticker=%s)' %
                                            (self.name, ticker))

    def get_market_price(self, ticker):
        """(dict) Retrives a security's market price."""
        return self.get_book(ticker)['market_price']

    def get_price_history(self, ticker):
        """(dict) Retrives a security's market price history."""
        return self.get_book(ticker)['price_history']

    def get_wallet_history_df(self):
        """Retrives a security's market price history in a DataFrame object.

        Returns:
            DataFrame: The DataFrame object containing the robot's wallet
                history data.

        """
        hist = {item['time']: item['value'] for item in self.wallet_history}
        return pd.DataFrame.from_dict(hist, orient='index', dtype=float)

    def run(self):
        """The thread responsible for continuously executing the strategy."""
        self.strategy_fun()

    def _random_strategy(self):
        """A purely random strategy with a random order price."""
        while True:
            self.update_status()
            self.send_order(ticker=random.choice(self.get_all_tickers()),
                            side=random.choice(['buy', 'sell']),
                            size=100,
                            price=random.uniform(0.01, int(self.wallet) / 100),
                            # market_order=random.choice([True, False]))
                            market_order=False)
            time.sleep(random.uniform(1, 10))

    def _random_strategy_market(self):
        """A purely `at market price` random strategy."""
        while True:
            self.update_status()
            self.send_order(ticker=random.choice(self.get_all_tickers()),
                            side=random.choice(['buy', 'sell']),
                            size=100,
                            # market_order=random.choice([True, False]))
                            market_order=True)
            time.sleep(random.uniform(1, 20))

    def _get(self, uri):
        """Executes a GET request to the Stock Exchange address.

        Args:
            uri (str): The view URI.

        Returns:
            dict: the response's dict formatted JSON.

        """
        return json.load(urllib.request.urlopen(self.server_addr + uri))

    def _post(self, uri, message_data):
        """Executes a POST request to the Stock Exchange address.

        Args:
            uri (str): The view URI.
            message_data (dict): A dict representing the JSON data to be sent
                to the server.

         Returns:
            dict: the response's dict formatted JSON.

        """
        payload = json.dumps(message_data).encode('utf8')
        req = urllib.request.Request(self.server_addr + uri,
                                     headers={'Content-Type':
                                              'application/json'},
                                     data=payload, method='POST')
        with urllib.request.urlopen(req) as f:
            return json.load(f)

    def _random_name(self, size=5):
        """Generates a random robot trader name.

        The generated ticker will have the form Robot-<characters>.

        Examples:
            Robot-E2Q8V, Robot-I9KB3

        Keyword Args:
            size (int, default=5): the number of characters used on the random
                name.

        Returns:
            str: the random robot name.

        """
        return 'Robot-' + ''.join(random.choices(string.ascii_uppercase +
                                                 string.digits, k=size))

    def _parse_response(self, response, message):
        """Parses the recieved response from the Stock Exchange Server.

        Args:
            response (dict): The resulting request dict.
            message (str): The message to be inserted on the Exception in case
                the response is a failure.

        Returns:
            (object): the response data.

        Raises:
            Exception: If the respose wasn't successful.

        """
        if response['success']:
            return response['data']
        else:
            raise Exception(message)
