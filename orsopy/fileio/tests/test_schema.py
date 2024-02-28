import json
import unittest
import sys

from pathlib import Path

import jsonschema
import numpy as np
import yaml

from orsopy import fileio
from orsopy.fileio.base import _read_header_data, _validate_header_data

pth = Path(__file__).absolute().parent


class TestSchema(unittest.TestCase):
    def test_example_ort(self):
        schema_pth = pth / ".." / "schema" / "refl_header.schema.json"
        with open(schema_pth, "r") as f:
            schema = json.load(f)

        dct_list, data, version = _read_header_data(pth / "test_example.ort", validate=True)
        assert data[0].shape == (2, 4)
        assert version == "0.1"

        # d contains datetime.datetime objects, which would fail the
        # jsonschema validation, so force those to be strings.
        modified_dct_list = [json.loads(json.dumps(dct, default=str)) for dct in dct_list]
        for dct in modified_dct_list:
            jsonschema.validate(dct, schema)

        # try a 2 dataset file
        dct_list, data, version = _read_header_data(pth / "test_example2.ort", validate=True)
        assert len(dct_list) == 2
        assert dct_list[1]["data_set"] == "spin_down"
        assert data[1].shape == (4, 4)
        np.testing.assert_allclose(data[1][2:], data[0])

    def test_empty_ort(self):
        test = fileio.Orso.empty()
        _validate_header_data([test.to_dict()])

    def test_wrong_schema(self):
        vi = sys.version_info

        with self.assertRaises(jsonschema.exceptions.ValidationError):
            _validate_header_data([{}])
        test = fileio.Orso.empty()

        test.columns[0].unit = "test_fail_unit"
        if vi.minor < 7:
            with self.assertWarns(fileio.base.ORSOSchemaWarning):
                _validate_header_data([test.to_dict()])
        else:
            with self.assertRaises(jsonschema.exceptions.ValidationError):
                _validate_header_data([test.to_dict()])

        test.columns[0].unit = "1/nm"
        _validate_header_data([test.to_dict()])
        test.columns[1].name = "NotRightColumn"

        if vi.minor < 7:
            with self.assertWarns(fileio.base.ORSOSchemaWarning):
                _validate_header_data([test.to_dict()])
        else:
            with self.assertRaises(jsonschema.exceptions.ValidationError):
                _validate_header_data([test.to_dict()])
