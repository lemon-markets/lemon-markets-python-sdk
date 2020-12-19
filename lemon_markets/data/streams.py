import datetime
import json
import multiprocessing
from time import time
from typing import Callable

from websocket import create_connection

from lemon_markets.common.errors import StreamError
from lemon_markets.settings import DEFAULT_STREAM_API_URL


class BaseSerializer:
    json_content: dict = None

    def __init__(self, message: str):
        self.json_content = json.loads(message)
        self.__check_for_error()

    def __check_for_error(self):
        if self.json_content.get("error"):
            raise StreamError(detail=self.json_content.get("message"))

        if not self.json_content:
            raise StreamError(detail="Unknown error")

    def to_representation(self):
        output_dict: dict = {}
        for key, value in self.__dict__.items():
            if value and key != "json_content":
                output_dict[key] = value
        return output_dict

    def __repr__(self):
        output = self.to_representation()
        return str(self.__class__.__name__) \
            + "(" + ", ".join(["{}={}".format(key, value) for key, value in output.items()]) \
            + ")"


class Quote(BaseSerializer):
    '''A class representing a Quote

    Attributes:
        isin (str): The isin of the instrument
        bid_price (float): The bid price
        ask_price (float): The ask price
        date (datetime.datetime): The datetime of the quote (will yield human-readable string if printed)
        bid_quantity (int): The quantity of the bid
        ask_quantity (int): The quantity of the ask
        specifier (str): The mode in which the quote price is delivered. See :doc:`specifiers`

    Note:
        The descriptions may be incomplete
    '''
    def __init__(self, message, subscribed):
        super().__init__(message)
        self.isin = self.json_content.get("isin")
        self.bid_price = self.json_content.get("bid_price")
        self.ask_price = self.json_content.get("ask_price")
        self.date = datetime.datetime.fromtimestamp(float(self.json_content.get("date")))
        self.bid_quantity = self.json_content.get("bid_quan")
        self.ask_quantity = self.json_content.get("ask_quan")
        self.specifier = subscribed[self.isin]


class Tick(BaseSerializer):
    '''A class representing a single Tick

    Attributes:
        isin (str): The isin of the instrument
        quantity (int): The quantity
        price (float): The price at the time
        date (datetime.datetime): The datetime of the tick (will yield human-readable string if printed)
        side (int): The side (buy or sell)
        specifier (str): The mode in which the tick price is delivered. See :doc:`specifiers`

    Note:
        The descriptions may be incomplete
    '''
    def __init__(self, message, subscribed):
        super().__init__(message)
        self.isin = self.json_content.get("isin")
        self.price = self.json_content.get("price")
        self.quantity = self.json_content.get("quantity")
        self.date = datetime.datetime.fromtimestamp(float(self.json_content.get("date")))
        self.side = self.json_content.get("side")
        self.specifier = subscribed[self.isin]


class WSWorker(multiprocessing.Process):
    _last_message_time = 0

    def __init__(self, keepalive, restart, subscribed, serializer,
                 connect_url, typ3, callback, timeout, frequency_limit):
        super().__init__(target=self)
        self._keepalive = keepalive
        self._restart = restart
        self._subscribed = subscribed
        self._serializer = serializer
        self._connect_url = connect_url
        self._type = typ3
        self._callback = callback
        self._timeout = timeout
        self._frequency_limit = frequency_limit

    def run(self):
        while self._keepalive.value:
            self._restart.value = False
            ws = create_connection(self._connect_url,
                                   self._timeout)
            for each in self._subscribed.keys():
                ws.send(json.dumps({
                                  "action": "subscribe",
                                  "type": self._type,
                                  "specifier": self._subscribed[each],
                                  "value": each
                              }))
            while self._keepalive.value and not self._restart.value:
                if not (time() - self._last_message_time > self._frequency_limit):
                    continue
                try:
                    serialized = self._serializer(ws.recv(), self._subscribed)
                except Exception:
                    break
                self._callback(serialized)
                self._last_message_time = time()
            ws.close()


class StreamBase():
    _serializer = _connect_url = _type = _specifiers = _default_specifier = None

    def __init__(self, callback: Callable, timeout: float = 10, frequency_limit: float = 0):
        self._timeout = timeout
        self._frequency_limit = frequency_limit
        manager = multiprocessing.Manager()
        self._subscribed = manager.dict()
        self._keepalive = manager.Value('B', True)
        self._restart = manager.Value('B', False)

        self._ws_process = WSWorker(self._keepalive, self._restart,
                                    self._subscribed, self._serializer,
                                    self._connect_url, self._type,
                                    callback, self._timeout,
                                    self._frequency_limit)
        self._ws_process.daemon = True
        self._keepalive.value = True
        self._ws_process.start()

    def __del__(self):
        try:
            self._keepalive.value = False
            self._ws_process.join()
            del self._manager
        except Exception:
            pass

    def subscribe(self, isin: str, specifier: str = None):
        if specifier is None:
            specifier = self._default_specifier
        assert specifier in self._specifiers, 'Unsupported specifier!'
        if isin in self._subscribed.keys():
            return
        self._subscribed[isin] = specifier
        self._restart.value = True

    def unsubscribe(self, isin: str):
        del self._subscribed[isin]
        self._restart.value = True


class TickStream(StreamBase):
    '''A wrapper for the marketdata endpoint

    Args:
        callback (Callable, required): The function to call when new data is received
        timeout (float, optional): How many seconds for no data has to be received to trigger an automatic reconnect. Default is 10
        frequency_limit (float, optional): If set, the maximum frequency at which the callback can be called

    Note:
        The callback has to accept one parameter. This parameter will be passed a :class:`lemon_markets.data.streams.Tick` object
        representing the received tick
    '''
    _connect_url = DEFAULT_STREAM_API_URL+'marketdata/'
    _type = 'trades'
    _serializer = Tick
    _specifiers = ['with-quantity', 'with-uncovered', 'with-quantity-with-uncovered']
    _default_specifier = 'with-uncovered'


class QuoteStream(StreamBase):
    '''A wrapper for the quotes endpoint

    Args:
        callback (Callable, required): The function to call when new data is received
        timeout (float, optional): How many seconds for no data has to be received to trigger an automatic reconnect. Default is 10
        frequency_limit (float, optional): If set, the maximum frequency at which the callback can be called

    Note:
        The callback has to accept one parameter. This parameter will be passed a :class:`lemon_markets.data.streams.Quote`
        object representing the received quote
    '''
    _connect_url = DEFAULT_STREAM_API_URL+'quotes/'
    _type = 'quotes'
    _serializer = Quote
    _specifiers = ['with-quantity', 'with-price', 'with-quantity-with-price']
    _default_specifier = 'with-price'
