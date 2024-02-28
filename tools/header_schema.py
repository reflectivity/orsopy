"""
Generates the schema for an ORSO file,
based on the Orso class (from orsopy.fileio.orso)
"""
from copy import deepcopy
import os
from typing import Dict, List

from pydantic import TypeAdapter
from pydantic.json_schema import GenerateJsonSchema, JsonSchemaValue
from pydantic_core import core_schema

import orsopy
from orsopy.fileio import Orso, Column, ErrorColumn, ORSO_VERSION

# allow None as a value for any attribute
ALLOW_NULL_ANYWHERE = True

class OrsoGenerateJsonSchema(GenerateJsonSchema):
    # def generate(self, schema, mode='validation'):
    #     json_schema = super().generate(schema, mode=mode)
    #     json_schema['title'] = 'ORSO Reflectivity Format Schema'
    #     json_schema['$schema'] = self.schema_dialect
    #     return json_schema
    
    def dataclass_schema(self, schema: core_schema.DataclassSchema) -> JsonSchemaValue:
        json_schema = super().dataclass_schema(schema)
        for prop, value in json_schema.get('properties', {}).items():
            # make the schema accept None as a value for any of the
            # Header class attributes.
            value.pop('title', None)
            if ALLOW_NULL_ANYWHERE:
                if 'enum' in value and not None in value['enum']:
                    value['enum'].append(None)
                if 'type' in value:
                    value['anyOf'] = [{'type': value.pop('type')}]
                if "anyOf" in value and not {"type": "null"} in value['anyOf']:
                    value['anyOf'].append({'type': 'null'})

        return json_schema


ADD_COLUMN_ORDER = True
COLUMN_ORDER = ["Qz", "R"]
ERROR_COLUMN_ORDER = ["sR", "sQz"]
SCHEMA_URL = "https://raw.githubusercontent.com/reflectivity/orsopy/v{}/orsopy/fileio/schema/refl_header.schema.json"
DEFINITIONS_KEY = "$defs"

column_schema = TypeAdapter(Column).json_schema()
# TODO: set proper enum for unit, this will fail for additional columns e.g. wavelength
column_schema["properties"]["unit"] = {"enum" : [None, "1/nm", "1/angstrom", "1", "1/s"]}
error_column_schema = TypeAdapter(ErrorColumn).json_schema()


def add_column_ordering(schema: Dict, column_order: List[str] = COLUMN_ORDER, error_column_order: List[str] = ERROR_COLUMN_ORDER):
    """
    Add constraints for the order of column names
    (note: modifies schema dict in-place)

    NOTE: this is done here, instead of in the type definition of Orso.columns
    because this type of constraint is not possible at the moment with python typing:
    specifying the first N elements of a Tuple or List but allowing additional
    elements to be something else.
    On the other hand, it is possible in JSON schema using "items" and "additionalItems"
    (or in more recent versions of the schema language, "prefixItems" and "items")
    """
    columns = {}
    for cname in column_order:
        cdef = deepcopy(column_schema)
        cdef["title"] = cname
        cdef["properties"]["name"] = {"enum": [cname]}
        columns[f"{cname}_column"] = cdef

    for cname in error_column_order:
        cdef = deepcopy(error_column_schema)
        cdef["title"] = cname
        cdef["properties"]["name"] = {"enum": [cname]}
        columns[f"{cname}_column"] = cdef

    schema[DEFINITIONS_KEY].update(columns)
    schema["properties"]["columns"]["prefixItems"] = [
        {"$ref": f"#/{DEFINITIONS_KEY}/{cname}_column"} for cname in (column_order + error_column_order)
    ]
    schema["properties"]["columns"]["items"] = {
        "anyOf": [
             {"$ref": f"#/{DEFINITIONS_KEY}/Column"},
             {"$ref": f"#/{DEFINITIONS_KEY}/ErrorColumn"},
        ]
    }
   

def main():
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": SCHEMA_URL.format(ORSO_VERSION),
    }
    orso_schema = TypeAdapter(Orso).json_schema(schema_generator=OrsoGenerateJsonSchema)
    schema.update(orso_schema)
    if ADD_COLUMN_ORDER:
        add_column_ordering(schema)

    schema_path = os.path.join(os.path.dirname(orsopy.__file__), "fileio", "schema")

    # generate json schema, and write out:
    json_output_file = os.path.join(schema_path, "refl_header.schema.json")
    print(f"writing JSON schema: {json_output_file}")
    import json

    open(json_output_file, "wt").write(
        json.dumps(schema, indent=2)
    )

    # generate yaml schema, and write out:
    yaml_output_file = os.path.join(schema_path, "refl_header.schema.yaml")
    print(f"writing YAML schema: {yaml_output_file}")
    import yaml

    open(yaml_output_file, "w").write(
        yaml.dump(schema)
    )


if __name__ == "__main__":
    main()
