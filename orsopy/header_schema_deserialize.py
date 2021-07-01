import datetime
import enum
from typing import Optional, Union, List, Literal, Dict, Any
from dataclasses import field
from dataclasses_json import dataclass_json

GENERATE_SCHEMA = False

def d(t):
    return field(metadata={"description": t})

if GENERATE_SCHEMA:
    from pydantic.dataclasses import dataclass as _dataclass

    class Config:
        @staticmethod
        def schema_extra(schema: Dict[str, Any]) -> None:
            for prop in schema.get('properties', {}).values():
                prop.pop('title', None)

    dataclass = _dataclass(config=Config)
else:
    from dataclasses import dataclass

@dataclass_json
@dataclass
class Creator:
    name: str
    affiliation: str
    time: datetime.datetime = d("timestamp string, formatted as ISO 8601 datetime")
    computer: str

@dataclass_json
@dataclass
class Sample:
    name: str
    
@dataclass_json
@dataclass
class Experiment:
    instrument: str
    probe: Union[Literal['neutron', 'xray']]
    sample: Sample

class Polarisation(str, enum.Enum):
    """ The first symbol indicates the magnetisation direction of the incident beam.
    An optional second symbol indicates the direction of the scattered beam, if a spin analyser is present."""
    p = '+'
    m = '-'
    mm = '--'
    mp = '-+'
    pm = '+-'
    pp = '++'

@dataclass_json
@dataclass
class Value:
    magnitude: Union[float, List[float]]
    unit: Optional[str] = field(default=None, metadata={"description": "SI unit string"})
    
@dataclass_json
@dataclass
class ValueRange:
    min: float
    max: float
    steps: Optional[int] = None
    unit: Optional[str] = field(default=None, metadata={"description": "SI unit string"})
    
@dataclass_json
@dataclass
class Measurement:
    scheme: str
    omega: Union[Value, ValueRange] = d("probe angle of incidence")
    wavelength: Union[Value, ValueRange]
    polarisation: Optional[Polarisation] = None
    
@dataclass_json
@dataclass
class DataSource:
    owner: str
    facility: str
    experimentID: str
    experimentDate: str
    title: str
    experiment: Experiment
    measurement: Measurement
    
@dataclass_json
@dataclass
class Column:
    """
    Information on a data column.
    """
    
    name: str = d("The name of the column")
    unit: Optional[str] = field(default="dimensionless", metadata={"description": "SI unit string"})
    description: Optional[str] = field(default=None, metadata={"description": "A description of the column"})

@dataclass_json
@dataclass
class ORSOHeader:
    creator: Creator
    data_source: DataSource
    columns: List[Column]
    

if GENERATE_SCHEMA:
    schema = ORSOHeader.__pydantic_model__.schema()
    print(schema)
    import json
    open("refl_header.schema.json", 'wt').write(json.dumps(schema, indent=2))

    import yaml
    open("refl_header.schema.yaml", 'w').write(yaml.dump(schema))
