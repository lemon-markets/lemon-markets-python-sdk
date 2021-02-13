import datetime
from typing import get_type_hints, Any

import pytz

from lemon_markets.common.errors import RestApiError
from lemon_markets.common.requests import ApiRequest


class AbstractApiObject:
    _data: dict

    class Fields:
        pass

        @classmethod
        def __getitem__(cls, item):
            return getattr(cls, item)

    def __init__(self, **kwargs):
        if kwargs:
            self.set_data(kwargs)

    def __setattr__(self, key, value):
        super().__setattr__(key, value)

    def set_data(self, data: dict):
        for key, value in data.items():
            if type(value) == dict:
                setattr(self, key, get_type_hints(self.Fields)[key](**value))
                continue
            if type(value) == list:
                attribute_value = [get_type_hints(self.Fields)[key].__args__[0](**item)
                                   if type(item) == dict or type(item) == list else item
                                   for item in value]
                setattr(self, key, attribute_value)
                continue

            if get_type_hints(self.Fields).get(key) and get_type_hints(self.Fields)[key] == datetime.datetime:
                if value:
                    if type(value) in (int, float):
                        timestamp_value = datetime.datetime.fromtimestamp(value, tz=pytz.timezone("UTC"))
                    else:
                        timestamp_value = value
                else:
                    timestamp_value = None
                setattr(self, key, timestamp_value)
                continue

            setattr(self, key, value)
        return self


class AbstractApiObjectMixin(AbstractApiObject):

    def retrieve(self):
        """
        Retrieve general information about an object. Has to be implemented by subclass.
        """
        raise NotImplementedError()

    def _build_object(self, request: ApiRequest):
        response_copy = request.response.copy()
        if request._account:
            response_copy["account"] = request._account
        if request.authorization_token:
            response_copy["authorization_token"] = request.authorization_token

        self.set_data(response_copy)
        return self

    def to_representation(self) -> str:
        if hasattr(self, "uuid"):
            return self.uuid
        return ""

    def __repr__(self):
        return "{} Object: {}".format(self.__class__.__name__, self.to_representation())

    def __str__(self):
        return self.to_representation()


class ListIterator:
    results: list = []
    _request: ApiRequest
    _object_class = None

    def __init__(self, request: ApiRequest, object_class):
        self._request = request
        self._object_class = object_class

        if not type(self._request.response) == dict and not self._request.response.get("results"):
            raise RestApiError(detail="Unexpected API response. Should be list.")

        self.__build_results()

    def __build_results(self):
        results = []
        for response_item in self._request.response.get("results", []):
            response_copy = response_item.copy()

            # add account and authorization token to the object in order to make requests in the future on this object
            # possible
            if self._request._account:
                response_copy["account"] = self._request._account
            if self._request.authorization_token:
                response_copy["authorization_token"] = self._request.authorization_token
            results.append(self._object_class(**response_copy))
            # results.append(self._object_class().set_data(response_item))
        self.results = results

    def next(self):
        pass


class ListMixin:
    _list_endpoint: str = ""

    @staticmethod
    def _build_query_params(**kwargs) -> dict:
        params = {}
        for param, value in kwargs.items():
            if param in ("authorization_token", "account", "list_endpoint"):
                continue

            if type(value) == list and value:
                params[param] = ','.join(map(str, value))  # url encode for backend
                continue

            if type(value) == datetime.datetime and value:
                params[param] = int(value.timestamp())
                continue

            if value:
                params[param] = value
        return params

    def set_data(self, data):
        """
        Implemented by concrete subclass or by AbstractApiObject class (right hand import)
        :return:
        """
        raise NotImplementedError()

    @staticmethod
    def list(object_class: Any, **kwargs) -> ListIterator:
        query_dict = ListMixin._build_query_params(**kwargs)

        request_arguments = {
            "endpoint": object_class._list_endpoint if not kwargs.get("list_endpoint") else kwargs.get("list_endpoint"),
            "method": "GET",
            "url_params": query_dict,
        }
        if kwargs.get("account"):
            request_arguments["account"] = kwargs["account"]

        if kwargs.get("ignore_account_url"):
            request_arguments["ignore_account_url"] = kwargs["ignore_account_url"]

        if kwargs.get("authorization_token"):
            request_arguments["authorization_token"] = kwargs["authorization_token"]

        request = ApiRequest(**request_arguments)
        iterator = ListIterator(request=request, object_class=object_class)
        return iterator
