from typing import Optional, List, Union
import datetime
from dataclasses import field, dataclass

from .base import Header, Person


@dataclass
class Creator(Header):
    """Creator"""
    name: str
    affiliation: Union[str, List[str]]
    computer: str
    time: Union[str, datetime.datetime]
