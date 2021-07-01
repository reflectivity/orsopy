import yaml
from dataclasses import asdict
from header_schema import ORSOHeader, Creator, DataSource, Experiment, Sample, Measurement, Value, ValueRange, Polarisation, Column
import datetime

creator = Creator(
    name="Jochen Stahn", 
    affiliation="PSI", 
    time=datetime.datetime(2020, 4, 6, 13, 21, 18), 
    computer="lnsa17.psi.ch")

data_source = DataSource(
    owner = "Jochen Stahn, PSI",
    facility = "Paul Scherrer Institut, SINQ",
    experimentID = "2019 0042",
    experimentDate = "2020/02/02 - 2020/02/04",
    title = "Generation of input for file formatting purposes",
    experiment = Experiment(
        instrument = "neutron reflectometer Amor",
        probe = "neutrons",
        sample = Sample(
            name = "Ni1000"
        )
    ),
    measurement = Measurement(
        scheme = "energy-dispersive",
        omega = Value(magnitude=1.2, unit="deg"),
        wavelength = ValueRange(min=4.0, max=12.5, unit="angstrom"),
        polarisation = Polarisation("+")
    )
)

columns = [
    Column(name="Qz", unit="1/angstrom", description= "WW transfer"),
    Column(name="R", description="reflectivity"),
    Column(name="sR", description="error-reflectivity"),
    Column(name="sQz", unit="1/angstrom", description="resolution-WW transfer"),
    Column(name="lambda", unit="angstrom", description="wavelength"),
    Column(name="omega", unit="deg", description="angle")
]

header = ORSOHeader(creator=creator, data_source=data_source, columns=columns)

header_str = yaml.dump(asdict(header))
print(header_str)