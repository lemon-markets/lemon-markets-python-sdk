import datetime
from typing import Union

from lemon_markets.account import Account
from lemon_markets.common.errors import BaseError
from lemon_markets.common.helpers import UUIDAccountObjectMixin, CreateMixin
from lemon_markets.common.objects import AbstractApiObjectMixin, ListMixin
from lemon_markets.common.requests import ApiRequest
from lemon_markets.instrument import Instrument


class OrderError(BaseError):
    pass


class Order(CreateMixin, UUIDAccountObjectMixin, AbstractApiObjectMixin, ListMixin):

    class Fields(AbstractApiObjectMixin.Fields):
        account: Account
        instrument: Instrument
        limit_price: float
        stop_price: float
        quantity: int
        valid_until: datetime.datetime
        created_at: datetime.datetime
        processed_at: datetime.datetime
        processed_quantity: int
        status: str
        side: str
        average_price: str
        uuid: str
        type: str

    def __init__(self,
                 account: Account = None,
                 instrument: Union[str, Instrument] = None,
                 quantity: int = None,
                 valid_until: Union[float, int, datetime.datetime] = None,
                 limit_price: float = None,
                 stop_price: float = None,
                 type: str = None,
                 side: str = None,
                 uuid: str = None,
                 **kwargs
                 ):
        super().__init__(
            account=account,
            instrument=instrument,
            quantity=quantity,
            valid_until=valid_until,
            limit_price=limit_price,
            stop_price=stop_price,
            type=type,
            side=side,
            uuid=uuid,
            **kwargs
        )

    def retrieve(self):
        self.check_instance()
        request = ApiRequest(
            endpoint="orders/{}/".format(self.uuid),
            account=self.account,
            method="GET"
        )

        self.set_data(request.response)
        return self

    def create(self):
        if self.uuid:
            raise OrderError(detail="Cannot create order as it already exists.")
        request = ApiRequest(
            endpoint="orders/",
            account=self.account,
            method="POST",
            body=self._build_body()
        )

        self.set_data(request.response)

    def destroy(self, raise_exception: bool = False) -> bool:
        try:
            self.check_instance()
            ApiRequest.__init__(
                endpoint="orders/{}/".format(self.uuid),
                account=self.account,
                method="DELETE"
            )
            return True
        except Exception as e:
            if raise_exception:
                raise e
            else:
                return False

    def execute(self):
        return self.create()

    def delete(self, raise_exception: bool = False) -> bool:
        """
        Redirects to destroy method. This method is only for convenience.
        :param raise_exception:
        :return:
        """
        return self.destroy(raise_exception=raise_exception)

    @staticmethod
    def list(account: Account, ordering: str = "-created_at", limit: int = None, offset: int = None):
        return ListMixin.list(object_class=Order, account=account, ordering=ordering, limit=limit, offset=offset,
                              list_endpoint="orders/")

    @property
    def is_executed(self) -> bool:
        """
        Tells you whether your order was fully executed. For partially executed orders, this returns False as well.
        This property does not check the current status.
        :return: {bool}
        """
        if hasattr(self, "status") and self.status == "executed":
            return True
        return False

    def check_if_executed(self) -> bool:
        """
        Retrieves the current order status and checks its status
        :return:
        """
        if not self.is_executed:
            self.retrieve()
        return self.is_executed
