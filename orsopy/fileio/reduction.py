"""
The reduction elements for the ORSO header
"""

# author: Andrew R. McCluskey (arm61)

from typing import Optional, List, Union
from dataclasses import field
import datetime
from .base import Header, Person


class Software(Header):
    """
    Software description.

    :param name: Software name.
    :param version: Version identified for the software.
    :param platform: Operating system.
    """
    name: str
    version: Optional[str] = None
    platform: Optional[str] = None


class Reduction(Header):
    """
    A description of the reduction that has been performed.

    :param software: Software used for reduction.
    :param timestamp: Datetime of reduced file creation.
    :param creator: The person or routine who created the reduced file.
    :param computer: Name of the reduction machine.
    :param call: Command line call or similar.
    :param script: Path to reduction script or notebook.
    :param binary: Path to full reduction information file.
    """
    software: Union[Software, str]
    timestamp: Optional[datetime.datetime] = field(
        default=None,
        metadata={
            "description": "Timestamp string, formatted as ISO 8601 datetime"
        })
    creator: Optional[Person] = None
    corrections: Optional[List[str]] = None
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

    __repr__ = Header._staggered_repr
