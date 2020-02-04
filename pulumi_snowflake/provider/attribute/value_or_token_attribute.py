from typing import Tuple

from .base_attribute import BaseAttribute
from ...token import Token


class ValueOrTokenAttribute(BaseAttribute):
    """
    Represents a SQL attribute which can take some value, or a special token such as NONE or AUTO.
    This class is a decorator which wraps another `BaseAttribute` instance which provides the actual value if the
    special token is not given.
    """

    def __init__(self, attribute: BaseAttribute, token: Token):
        super().__init__(attribute.name, attribute.required)
        self.attribute = attribute
        self.token = token

    def generate_sql(self, value) -> str:
        if value == self.token:
            return f"{self.sql_name} = {self.token.sql}"
        else:
            return self.attribute.generate_sql(value)

    def generate_bindings(self, value) -> Tuple:
        if value == self.token:
            return None
        else:
            return self.attribute.generate_bindings(value)