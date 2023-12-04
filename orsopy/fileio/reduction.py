"""
The reduction elements for the ORSO header
"""

import datetime

from dataclasses import field, dataclass
from typing import List, Optional, Union

from .base import Header, Person


@dataclass
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

    comment: Optional[str] = None

    yaml_representer = Header.yaml_representer_compact

    def __init__(self, name, version=None, platform=None, *, comment=None, **kwds):
        super(Software, self).__init__()
        self.name = name
        self.version = version
        self.platform = platform
        for k, v in kwds.items():
            setattr(self, k, v)
        self.comment = comment
        self.__post_init__()


@dataclass
class Reduction(Header):
    """
    A description of the reduction that has been performed.

    :param software: Software used for reduction.
    :param timestamp: Datetime of reduced file creation.
    :param creator: The person or routine who created the reduced file.
    :param corrections: A list of the corrections that have been performed.
    :param computer: Name of the reduction machine.
    :param call: Command line call or similar.
    :param script: Path to reduction script or notebook.
    :param binary: Path to full reduction information file.
    """

    software: Software
    timestamp: Optional[datetime.datetime] = field(
        default=None, metadata={"description": "Timestamp string, formatted as ISO 8601 datetime"}
    )
    creator: Optional[Person] = None
    corrections: Optional[List[str]] = None
    computer: Optional[str] = field(default=None, metadata={"description": "Computer used for reduction"})
    call: Optional[str] = field(default=None, metadata={"description": "The command line call used"})
    script: Optional[str] = field(default=None, metadata={"description": "Path to reduction script or notebook"})
    binary: Optional[str] = field(default=None, metadata={"description": "Path to full information file"})

    __repr__ = Header._staggered_repr

    comment: Optional[str] = None

    def __init__(
            self,
            software,
            timestamp=None,
            creator=None,
            corrections=None,
            computer=None,
            call=None,
            script=None,
            binary=None,
            *,
            comment=None,
            **kwds
    ):
        super(Reduction, self).__init__()
        self.software = software
        self.timestamp = timestamp
        self.creator = creator
        self.corrections = corrections
        self.computer = computer
        self.call = call
        self.script = script
        self.binary = binary
        for k, v in kwds.items():
            setattr(self, k, v)
        self.comment = comment
        self.__post_init__()
