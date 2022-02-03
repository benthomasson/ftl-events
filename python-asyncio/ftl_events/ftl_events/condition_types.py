
from typing import NamedTuple

class Integer(NamedTuple):
    value: int


class String(NamedTuple):
    value: str


class Identifier(NamedTuple):
    value: str


class OperatorExpression(NamedTuple):
    left: str
    operator: str
    right: str
