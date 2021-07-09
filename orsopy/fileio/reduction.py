"""
The reduction elements for the ORSO header
"""

# author: Andrew R. McCluskey (arm61)

from typing import Optional, List
from dataclasses import field, dataclass
import datetime
from .base import Header, Person


@dataclass
class Software(Header):
    """Description of the reduction software."""
    name: str
    version: str
    platform: str
    _orso_optionals = []


@dataclass
class Reduction(Header):
    """A description of the reduction that has been performed."""
    software: Software
    timestamp: datetime.datetime = field(
        metadata={
            "description": "Timestamp string, formatted as ISO 8601 datetime"
        })
    creator: Person
    corrections: List[str]
    computer: Optional[str] = field(
        default=None, metadata={'description': 'Computer used for reduction'})
    call: Optional[str] = field(
        default=None, metadata={'description': 'The command line call used'})
    script: Optional[str] = field(
        default=None,
        metadata={'description': 'Path to reduction script or notebook'})
    binary: Optional[str] = field(
        default=None,
        metadata={'description': 'Path to full information file'})
    _orso_optionals = ['computer', 'call', 'script', 'binary']
