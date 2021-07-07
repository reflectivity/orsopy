"""
The reduction elements for the ORSO header
"""

# author: Andrew R. McCluskey (arm61)

from typing import Optional, List
from dataclasses import field, dataclass
import datetime
from dataclasses_json import dataclass_json
from .base import Header, Person


@dataclass_json
@dataclass
class Software(Header):
    """Description of the reduction software."""
    name: str
    version: str
    platform: str
    orso_optionals = []


@dataclass_json
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
    orso_optionals = ['computer', 'call', 'script', 'binary']
