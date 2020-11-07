# Welcome

This is the official lemon.markets SDK. With this SDK you can do everything which is possible on the lemon.markets API in an easier way, e.g.
- create, list and retrieve orders or transactions
- list your portfolio
- retrieve account details, current cash etc.
- get historical marketdata and real-time orderbook & ticks data

You can find the raw API documentation over here: [documentation.lemon.markets](https://documentation.lemon.markets/)

## Get Started

To use our API, you have to sign up on [lemon.markets](https://app.lemon.markets/register). 
lemon.markets is completely free, we don't charge for market data or whatsoever. If you take part in our beta trading competition, you will even get the chance to win money!

Installing this SDK is super easy, just run 
```pip install lemon-markets-sdk``` and you're good to go.

### Token

For every API request, you need to have an API Access Token. You can generate one on the dashboard when creating a strategy.

Your token looks like this one: `3c1c7343b6c8c241ebeedcb2a92095ba20dc692d`

To use the token, import the Token class, instantiate it and the SDK will do the rest:

```python
from lemon_markets.token import Token

my_token = Token("3c1c7343b6c8c241ebeedcb2a92095ba20dc692d")
```

Your account is linked to your token, so if you want to get the account details, just do this:
```python
my_account = token.account
```

### Account

If you want to **list** all accounts (you should only have one at the moment - the demo one):

```python
from lemon_markets.account import Account

all_accounts = Account.list(authorization_token=my_token)

my_account = all_accounts.results[0]  # this one should be the demo account
```

If you want to **retrieve** a single account, grab it by its uuid:

```python
from lemon_markets.account import Account

my_account = Account(uuid='76a42cea-a144-488f-afc2-a6fb967c3ab2', authorization_token=my_token)
```


There are a couple of very useful things you can perform on an account:

```python
my_account.cash_in_invest  # gets the cash you have at hand (total balance minus open order volume)
my_account.total_balance  # gets your total cash
my_account.fetch_account_state()  # updates your cash_to_invest and total_balance
```

### Orders

One important thing you wanna do with our API is **creating** an order. So here we go:

```python
from lemon_markets.order import Order
import datetime

new_order = Order(
                  instrument="DE0007100000",  # ISIN for Daimler, you can pass an instrument instance in here as well
                  quantity=10,
                  side="buy",
                  limit_price=50.00,
                  valid_until=datetime.datetime.now() + datetime.timedelta(days=1),
                  account=my_account
                 )
                 
new_order.create()
```
You need to pass the account instance from the previous step to the Order class. The account instance is needed as you create an order on behalf of an account. You don't need to pass the token instance as the account is already linked to the token.

After your order has been created, you can check the execution status by accessing the is_executed attribute, e.g. `new_order.is_executed`. 
You can refresh the status by executing `new_order.check_if_executed()`.

After creating, an order has the following attributes:
| attribute | value |
| ------ | ------ |
| uuid | custom UUID per order (str) |
| date_created | datetime object of the date created |
| instrument | Instrument object |
| quantity | quantity (int) |
| side | buy / sell (str) |
| type | market/ stop_market / limit / stop_limit (str) |
| processed_at | datetime object of the latest processing time |
| processed_quantity | can be lower than the expected quantity due to a partial exec. (int) |
| average_price | execution price (float) |
| valid_until | datetime object of the valid until time |
| status | open / in_process / expired / deleted / executed (str) |



**List** all your orders:

```python
from lemon_markets.order import Order

all_orders = Order.list(account=my_account)
all_orders.results
```
If your token is linked to a strategy, only orders of the strategy will be shown.

**Retrieve** a single order:

```python
from lemon_markets.order import Order
order = Order(account=my_account, uuid="76a42cea-a144-488f-afc2-a6fb967c3ab2")

order.retrieve()
```


### Portfolio

**List** all your portfolio items
```python
from lemon_markets.portfolio import Portfolio

portfolio = Portfolio.list(account=my_account)
```
Only the portfolio items listed in strategy your token is linked to will be shown.


## Market Data
You can either retrieve historical data through the lemon.markets Rest-API or real-time data through websockets.

#### Instruments
But first, you need to know which instruments (stocks, derivates, ETFs, bonds) are available on lemon.markets:

```python
from lemon_markets.instrument import Instrument

instruments = Instrument.list(authorization_token=my_token)
```

#### Historical data: OHLC 
We want to retrieve the OHLC (Open High Low Close) data for an instrument on a _M1_ basis (each minute):
```python
from lemon_markets.data.ohlc import M1

m1_data = M1.list(instrument="DE0007100000",authorization_token=my_token)  # you can pass an Instrument instance in here as well

```

#### Real-Time data: Websocket

1) Before receiving the data, we need to declare what should happen in that case. 
2) Second, we need to tell the stream that it should subscribe to an instrument.

To get ticks data:
```python
from lemon_markets.data.streams import TickStream

def on_message(socket, tick):
    print(tick)
    
tick_stream = TickStream(on_message=on_message)

def on_open(socket):
    tick_stream.subscribe("DE0007100000")  # when the socket is open, we would like to subscribe to the Daimler tick stream
    
tick_stream.on_open = on_open

tick_stream.run()  # this runs the socket forever/ until the connection interrups.

```

and to get L1 orderbook data (or so-called "quotes"):
```python
from lemon_markets.data.streams import QuoteStream

def on_message(socket, quote):
    print(quote)
    
quote_stream = QuoteStream(on_message=on_message)

def on_open(socket):
    quote_stream.subscribe("DE0007100000")  # when the socket is open, we would like to subscribe to the Daimler quote stream
    
quote_stream.on_open = on_open

quote_stream.run()
```

# To Do's

This SDK is not finished, but it is a good start. Feel free to contribute!
- documentation with readthedocs
- reconnecting websocket when the connection interrupts
- tests
- code documentation
- add list endpoint paginator

For any feedback, questions etc. feel free to reach out to info@lemon.markets or join our [Slack community](https://lemon.markets/community/)
