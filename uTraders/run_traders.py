#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A simple micro Stock Market Simulator trader robot usage example.

This is a very simple example of the usage of the RobotTrader class.

The commented section shows an example of how to plot a RobotTrader's wallet
history.

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

import matplotlib.pyplot as plt

from utrader import RobotTrader

rdn_traders = [RobotTrader() for _ in range(0, 10)]

for trader in rdn_traders:
    trader.start()

# rdn_traders[0].get_wallet_history_df().plot()
# plt.show()
