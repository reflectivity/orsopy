"""
Generates the schema for an ORSO file.

Author: Brian Maranville (NIST)
"""
import datetime
import enum
from typing import Optional, Union, List, Literal, Dict, Any, Tuple
from dataclasses import field

from pydantic import Field

GENERATE_SCHEMA = True


def d(t):
    return field(metadata={"description": t})


if GENERATE_SCHEMA:
    from pydantic.dataclasses import dataclass as _dataclass

    class Config:
        @staticmethod
        def schema_extra(schema: Dict[str, Any]) -> None:
            for prop, value in schema.get('properties', {}).items():
                value.pop("title", None)

                # make the schema accept None as a value for any of the
                # Header class attributes.
                if 'enum' in value:
                    value['enum'].append(None)

                if 'type' in value:
                    value['anyOf'] = [{'type': value.pop('type')}]
                    value['anyOf'].append({'type': 'null'})
                elif "anyOf" in value:
                    value['anyOf'].append({'type': 'null'})
                # only one $ref e.g. from other model
                elif '$ref' in value:
                    value['anyOf'] = [{'$ref': value.pop('$ref')}]

    dataclass = _dataclass(config=Config)
else:
    from dataclasses import dataclass


@dataclass
class Person:
    """Information about a person, including name, affilation(s), and email."""

    name: str
    affiliation: Union[str, List[str]]
    contact: Optional[str] = field(
        default=None, metadata={"description": "Contact (email) address"}
    )


@dataclass
class Creator(Person):
    time: datetime.datetime = field(
        default=None,
        metadata={"description": "timestamp string, formatted as ISO 8601 datetime"}
    )
    computer: str = ""


@dataclass
class Sample:
    name: str
    type: Optional[str] = field(default=None)
    composition: Optional[str] = field(default=None)
    description: Optional[Union[str, List[str], List[Any]]] = field(default=None)
    environment: Optional[Union[str, List[str], List[Any]]] = field(default=None)


@dataclass
class Experiment:
    title: str
    instrument: str
    date: Optional[datetime.datetime]
    probe: Union[Literal["neutrons", "x-rays"]]
    facility: Optional[str] = field(default=None)
    proposalID: Optional[str] = field(default=None)
    doi: Optional[str] = field(default=None)


# class Polarization(str, enum.Enum):
#     """The first symbol indicates the magnetisation direction of the incident beam.
#     An optional second symbol indicates the direction of the scattered beam, if a spin analyser is present."""
#
#     unpolarized = "unpolarized"
#     p = "+"
#     m = "-"
#     mm = "--"
#     mp = "-+"
#     pm = "+-"
#     pp = "++"


@dataclass
class File:
    file: str
    timestamp: datetime.datetime


@dataclass
class Value:
    magnitude: Union[float, List[float]]
    unit: Optional[str] = field(default=None, metadata={"description": "SI unit string"})


@dataclass
class ValueRange:
    min: float
    max: float
    unit: Optional[str] = field(default=None, metadata={"description": "SI unit string"})
    steps: Optional[int] = None


@dataclass
class InstrumentSettings:
    incident_angle: Union[Value, ValueRange]
    wavelength: Union[Value, ValueRange]
    polarization: Optional[Union[Literal['unpolarized', 'p', 'm', 'mm', 'mp', 'pm', 'pp']]] = field(
        default='unpolarized',
        metadata={
            'description':
                'Polarization described as unpolarized/ p / m / pp / pm / mp / mm / vector'
        })


@dataclass
class Measurement:
    instrument_settings: InstrumentSettings
    data_files: List[Union[File, str]]
    scheme: Optional[Union[
        Literal[
            "angle- and energy-dispersive",
            "angle-dispersive",
            "energy-dispersive",
        ]
    ]] = None


@dataclass
class Software:
    """Description of the reduction software."""
    name: str
    version: Optional[str] = None
    platform: Optional[str] = None


@dataclass
class Reduction:
    software: Union[Software, str]
    computer: Optional[str] = field(
        default=None, metadata={'description': 'Computer used for reduction'}
    )
    call: Optional[str] = ""
    timestamp: Optional[datetime.datetime] = field(
        default=None,
        metadata={
            "description": "Timestamp string, formatted as ISO 8601 datetime"
        })
    creator: Optional[Person] = None
    corrections: Optional[List[str]] = None
    call: Optional[str] = field(
        default=None, metadata={'description': 'The command line call used'})
    script: Optional[str] = field(
        default=None,
        metadata={'description': 'Path to reduction script or notebook'})
    binary: Optional[str] = field(
        default=None,
        metadata={'description': 'Path to full information file'})


@dataclass
class DataSource:
    owner: Person
    experiment: Experiment
    sample: Sample
    measurement: Measurement


@dataclass
class Column:
    """
    Information on a data column.
    """

    name: str = d("The name of the column")
    dimension: Optional[str] = ""
    unit: Optional[str] = field(
        default=None, metadata={"description": "SI unit string"}
    )
    # description: Optional[str] = field(
    #    default=None, metadata={"description": "A description of the column"})


@dataclass
class qz_column(Column):
    name: Literal["Qz"]
    unit: Literal["1/angstrom", "1/nm"]

@dataclass
class R_column(Column):
    name: Literal["R"]


@dataclass
class sR_column(Column):
    name: Literal["sR"]


@dataclass
class sQz_column(Column):
    name: Literal["sQz"]
    unit: Literal["1/angstrom", "1/nm"]


@dataclass
class ORSOHeader:
    creator: Creator
    data_source: DataSource
    columns: Union[
        Tuple[qz_column, R_column],
        Tuple[qz_column, R_column, sR_column],
        Tuple[qz_column, R_column, sR_column, sQz_column],
        Tuple[qz_column, R_column, sR_column, sQz_column, Column],
    ]
    reduction: Optional[Reduction] = None
    data_set: Union[str, int] = None


if GENERATE_SCHEMA:
    schema = ORSOHeader.__pydantic_model__.schema()
    print(schema)
    import json

    open("refl_header.schema.json", "wt").write(json.dumps(schema, indent=2))

    import yaml

    open("refl_header.schema.yaml", "w").write(yaml.dump(schema))
