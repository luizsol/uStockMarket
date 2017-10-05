# uStockMarket
A very simple stock market simulator

## Description

This project implements a very simple stock market into which the users should use a RESTful API in order to acquire market data and to send orders.

## Motivation

The purpose of this project is for me to acquire and develop skills on the Flask framework with the MongoDB database.

## Dependencies

- MongoDB
- Python 3.6
	- flask-0.12.2
	- flask-restful 0.3.6
	- pymongo-3.5.1
	- mongoengine-0.13.0
	- numpy
	- pandas
	- matplotlib

## Usage

The system as a hole is comprised of 3 parts:

- ***uStockMarket***: the webserver responsible for simulating the stock market itself
- ***uTraders***: a program that simulates various traders that will buy and sell stocks on the stock market
- ***uHomeBroker***: a program that emulates a simple home broker so the user can see the stock market data and send his own orders

### ***uStockMarket***

#### Setup

***Work in progress***

#### Starting the server
To start the `uStockExchange` server go to the [`uStockMarket`](uStockMarket) folder and execute the following command:

```shell
python server.py
```

Running the server on this manner will erase all existing database (if it exists) and create random securities.

In case you want to start the server and keep the existing database use the `-c False` flag.

Another option is to start the server with an yaml configuration file (passed with the `-f <path>` flag). An example of such configuration file can be found [here](uStockMarket/config_file_example.yaml).

To see all the command line flags, execute:

```shell
python server.py -h
```
#### Interacting

Once the server is up and runnig you can start interacting with it.

All interaction with the `uStockMarket` is made through a [RESTful](https://en.wikipedia.org/wiki/Representational_state_transfer) API (implemented on the [`server.py`](uStockMarket/server.py) file with the [Flask](http://flask.pocoo.org/) mircoframework), sending and recieving [JSON](https://en.wikipedia.org/wiki/JSON) documents by using `HTTP`'s `GET` and `POST` methods (a simple REST tutorial can be found [here](https://www.tutorialspoint.com/restful/)).

An easy way to interact with the server is by using a tool like [Postman](http://www.getpostman.com), with wich you can edit, send, recieve and visualize `JSON` data with `RESTful` webservices. Most of the examples here were generated using this tool.

##### Registering a new security

***Work in progress***

##### Registering a new trader

To register a new trader you must `POST` a `JSON` containing the trader data to the `/register_trader` URI.

Here is one example of a `JSON` document that was `POST`ed to `http://127.0.0.1:5000/register_trader`:

```json
{
	"name": "Luiz Sol",
    "wallet": 1223.23,
    "portfolio": {
    	"BBVA03": 12300
    }
}
```

And this is the response from the server:

```json
{
    "success": true,
    "data": {
        "name": "Luiz Sol",
        "wallet": "1223.23",
        "wallet_history": [],
        "portfolio": [
            {
                "trader": "Luiz Sol",
                "ticker": "BBVA03",
                "shares": "12300",
                "value": "0.00"
            }
        ],
        "portfolio_value": "0.00",
        "orders": []
    }
}
```

As you can see, the response is composed of two fields:
* `success`: whether the interaction was successful or not
* `data`: the data sent back from the server
* `message`: when a request fails the error message will be on this field

When we try to register the same user again, this is the recieved `JSON`:

```json
{
    "success": false,
    "message": "The Luiz Sol trader already exists."
}
```

##### Listing all registered traders

`GET` from `list_traders`:

Example result (http://127.0.0.1:5000/list_traders):
```json
{
    "success": true,
    "data": [
        "John Doe",
        "Jane Gin",
        "Robot-EDD6S",
        "Robot-DLKQP",
        "Robot-9ZWHL",
        "Robot-3XFQU",
        "Robot-Z7S7S",
        "Robot-M37V7",
        "Robot-UEXCK",
        "Robot-CGFVA",
        "Robot-58YG5",
        "Robot-N9LRC"
    ]
}
```

##### Listing all available securities

`GET` from `list_tickers`:

Example result (http://127.0.0.1:5000/list_tickers):
```json
{
    "success": true,
    "data": {
        "tickers": [
            "BBVA03",
            "LLCA13",
            "RRTV99",
            "KKLE64",
            "ASDF12"
        ]
    }
}
```

##### Retriving a trader status

`GET` from `trader_status/<trader_name>`:

Example result (http://127.0.0.1:5000/trader_status/Robot-NIXNZ):
```json
{
    "success": true,
    "data": {
        "name": "Robot-NIXNZ",
        "wallet": "1772.00",
        "wallet_history": [
            {
                "value": "3519.00",
                "time": "2017-10-04 21:58:49.643000",
                "amount": "None"
            },
            ...
            {
                "value": "1772.00",
                "time": "2017-10-04 22:03:21.630000",
                "amount": "None"
            }
        ],
        "portfolio": [
            {
                "trader": "Robot-NIXNZ",
                "ticker": "BBVA03",
                "shares": "80000",
                "value": "380000.00"
            },
            ...
            {
                "trader": "Robot-NIXNZ",
                "ticker": "ASDF12",
                "shares": "209900",
                "value": "3192579.00"
            }
        ],
        "portfolio_value": "5988625.00",
        "orders": [
            {
                "trader": "Robot-NIXNZ",
                "ticker": "ASDF12",
                "original_size": "100",
                "current_size": "100",
                "time": "2017-10-04 21:58:09.328000",
                "price": "2.81",
                "market_order": "False",
                "canceled": "False",
                "filled": "False",
                "fills": [],
                "order_type": "Bid"
            },
            {
                "trader": "Robot-NIXNZ",
                "ticker": "ASDF12",
                "original_size": "100",
                "current_size": "0",
                "time": "2017-10-04 21:58:09.328000",
                "price": "53.03",
                "market_order": "False",
                "canceled": "False",
                "filled": "True",
                "fills": [
                    {
                        "order": "59d583c0d940f269f7a67ea1",
                        "seller": "Robot-GMQFR",
                        "buyer": "Robot-NIXNZ",
                        "size": "100",
                        "price": "23.99",
                        "time": "2017-10-04 21:58:50.383000"
                    }
                ],
                "order_type": "Bid"
            },
            ...
            {
                "trader": "Robot-NIXNZ",
                "ticker": "BBVA03",
                "original_size": "100",
                "current_size": "0",
                "time": "2017-10-04 21:58:09.328000",
                "price": "4.75",
                "market_order": "False",
                "canceled": "False",
                "filled": "True",
                "fills": [
                    {
                        "order": "59d58411d940f269f7a67f45",
                        "seller": "Robot-NIXNZ",
                        "buyer": "Robot-0LN8T",
                        "size": "100",
                        "price": "4.75",
                        "time": "2017-10-04 22:03:21.589000"
                    }
                ],
                "order_type": "Ask"
            }
        ]
    }
}
```

##### Editing trader's positions

`POST` a `JSON` containing all new positions to `edit_positions`:

Example result (http://127.0.0.1:5000/trader_status/Robot-NIXNZ):

`POST`ed data:

```json
{
	"Robot-OCE3E":
    	{
            "RRTV99": 1000,
            "ASDF12": 2000
		},
	"John Doe":
    	{
            "KKLE64": 2000,
            "ASDF12": 4000,
            "BBVA03": 6000
    	}
}
```

Received data:
```json
{
    "success": true,
    "data": "Positions updated successfully."
}
```

##### Sending order

`POST` a `JSON` containing all order information to `send_order`.

The order informations are:
* `name`: the name of the trader sending the order
* `ticker`: the security code
* `side`: 'buy' or 'sell'
* `size`: the size of the order
* `market_order` (optional): whether the order should be executed 'at market price'
* `price` (optional): the price of each share on this order

It is important to notice that it's necessary to send either `market_order = true` or a price in every order.

Example result (http://127.0.0.1:5000/send_order):
`POST`ed data:

```json
{
	"trader": "John Doe",
	"ticker": "BBVA03",
	"side": "sell",
	"size": 3,
	"market_order": false,
	"price": 5.03
}
```

Received data:
```json
{
    "success": true,
    "data": {
        "trader": "John Doe",
        "ticker": "BBVA03",
        "original_size": "3",
        "current_size": "3",
        "time": "2017-10-04 16:29:07.191240",
        "price": "5.03",
        "market_order": "False",
        "canceled": "False",
        "filled": "False",
        "fills": [],
        "order_type": "Ask"
    }
}
```

##### Retrieving an Order Book data

`GET` from `book/<ticker>`:

Example result (http://127.0.0.1:5000/book/BBVA03):

```json
{
    "success": true,
    "data": {
        "ticker": "BBVA03",
        "market_price": "38.19",
        "top_bid": {
            "trader": "Robot-E2Q8V",
            "ticker": "BBVA03",
            "original_size": "100",
            "current_size": "100",
            "time": "2017-10-04 23:06:08.403000",
            "price": "77.50",
            "market_order": "False",
            "canceled": "False",
            "filled": "False",
            "fills": [],
            "order_type": "Bid"
        },
        "top_ask": {
            "trader": "Robot-I9KB3",
            "ticker": "BBVA03",
            "original_size": "100",
            "current_size": "100",
            "time": "2017-10-04 23:06:08.403000",
            "price": "106.11",
            "market_order": "False",
            "canceled": "False",
            "filled": "False",
            "fills": [],
            "order_type": "Ask"
        },
        "price_history": [
            {
                "value": "38.19",
                "time": "2017-10-04 23:06:53.942000",
                "amount": "100"
            },
            ...
        ]
    }
}
```

##### Retrieving a security market price history

`GET` from `price_history/<ticker>`:

Example result (http://127.0.0.1:5000/book/BBVA03):
```json
{
    "success": true,
    "data": [
        {
            "value": "42.30",
            "time": "2017-10-05 01:33:04.453000",
            "amount": "100"
        },
        ...
        {
            "value": "6.72",
            "time": "2017-10-05 01:50:08.761000",
            "amount": "100"
        }
    ]
}
```

##### Erasing all the database

`GET` from `clean_history`:

Example result (http://127.0.0.1:5000/clean_history):
```json
{
    "success": true,
    "data": "The database was erased."
}
```

### ***uTraders*** usage

This modules implement a micro Stock Market Simulator trader robot trades on the u_stock_market
system via it's `REST`ful API.

#### Usage

Once you have the uStockMarket server up and running you can start to make use of the `RobotTrader` classes. A good example of such usage is on the file [`uTraders/run_traders.py`](uTraders/run_traders.py):

```python
...

from utrader import RobotTrader

rdn_traders = [RobotTrader() for _ in range(0, 10)]

for trader in rdn_traders:
    trader.start()

...
```

By executing this module using the `-i` flag you can make use of these trading robots on the python interactive mode.

```shell
python -i run_traders.py
```

To see all available methods from the trading robots check the  [`uTraders/utrader.py`](uTraders/utrader.py) source code

### ***uHomeBroker*** usage
***Work in progress***



