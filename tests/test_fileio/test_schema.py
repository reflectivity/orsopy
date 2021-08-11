import json
import os.path
import jsonschema
import yaml
import orsopy
from orsopy.fileio.base import _read_header


class TestSchema:
    def test_example_ort(self):
        pth = os.path.dirname(orsopy.__file__)
        schema_pth = os.path.join(pth, "schema", "refl_header.schema.json")
        with open(schema_pth, "r") as f:
            schema = json.load(f)

        header = _read_header(os.path.join("tests", "test_example.ort"))
        d = yaml.safe_load(header)
        d = json.loads(json.dumps(d, default=str))
        jsonschema.validate(d, schema)
