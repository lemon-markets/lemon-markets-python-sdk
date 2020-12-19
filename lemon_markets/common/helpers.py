import datetime

from lemon_markets.common.errors import BaseError


class UUIDError(BaseError):
    detail = "An UUID is required in order to perform a retrieve request. Pass the UUID as parameter while " \
             "instantiation"


class UUIDObjectMixin:
    uuid: str

    def check_instance(self):
        if hasattr(self, "uuid"):
            return True
        raise UUIDError


class AccountError(BaseError):
    detail = "An Account is required in order to perform the retrieve request on behalf of the account."


class AccountObjectMixin:
    account: "Account"

    def check_instance(self):
        if hasattr(self, "account") and hasattr(self.account, "uuid"):
            return True
        raise AccountError


class UUIDAccountObjectMixin(AccountObjectMixin, UUIDObjectMixin):

    def check_instance(self):
        return UUIDObjectMixin.check_instance(self) and AccountObjectMixin.check_instance(self)


class CreateMixin:

    def _build_body(self) -> dict:
        primitive_types = (float, int, str, bool)
        body = {}
        for attribute, value in self.__dict__.items():
            if not value:
                continue

            if attribute == "account" or attribute == "_data" or attribute == "_list_endpoint":
                continue

            if type(value) in primitive_types:
                body[attribute] = value
                continue
            if type(value) == datetime.datetime:
                body[attribute] = value.timestamp()
                continue
            body[attribute] = value.to_representation()  # something like the Account or Order class

        return body
