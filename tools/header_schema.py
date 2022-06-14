"""
Generates the schema for an ORSO file,
based on the Orso class (from orsopy.fileio.orso)
"""
from copy import deepcopy
import os
import functools
from typing import Dict, List, Any

from pydantic.dataclasses import dataclass as _dataclass


class PydanticConfig:
    """ for schema generation, otherwise unused """
    @staticmethod
    def schema_extra(schema: Dict[str, Any]) -> None:
        for prop, value in schema.get('properties', {}).items():
            value.pop("title", None)

            # make the schema accept None as a value for any of the
            # Header class attributes.
            if 'enum' in value:
                value['enum'].append(None)

            if 'type' in value:
                value['type'] = [value.pop('type'), "null"]
            elif "anyOf" in value:
                value['anyOf'].append({'type': 'null'})
            # only one $ref e.g. from other model
            elif '$ref' in value:
                value['anyOf'] = [{'$ref': value.pop('$ref')}]

pydantic_dataclass = functools.partial(_dataclass, config=PydanticConfig)


ADD_COLUMN_ORDER = True
COLUMN_ORDER = ["Qz", "R", "sR", "sQz"]
SCHEMA_URL = "https://raw.githubusercontent.com/reflectivity/orsopy/v{}/orsopy/fileio/schema/refl_header.schema.json"


column_schema = {
    "title": "<cname>",
    "type": "object",
    "properties": {
        "name": {
            "enum": [
                "<cname>",
            ]
        },
        "unit": {"enum": ["1/angstrom", "1/nm", None]},
        "dimension": {
            "dimension": "dimension of column",
            "anyOf": [{"type": "string"}, {"type": "null"}],
        },
        "comment": {"anyOf": [{"type": "string"}, {"type": "null"}]},
    },
    "required": ["name"],
}


def add_column_ordering(schema: Dict, column_order: List[str] = COLUMN_ORDER):
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
        cdef["properties"]["name"]["enum"][0] = cname
        columns[f"{cname}_column"] = cdef

    schema["definitions"].update(columns)
    schema["properties"]["columns"]["items"] = [
        {"$ref": f"#/definitions/{cname}_column"} for cname in column_order
    ]
    schema["properties"]["columns"]["additionalItems"] = {
        "$ref": "#/definitions/Column"
    }

        

def main():
    # replace the dataclass function in the local import:
    from orsopy import dataclasses
    dataclasses.dataclass = pydantic_dataclass

    import orsopy
    from orsopy.fileio.orso import Orso, ORSO_VERSION

    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": SCHEMA_URL.format(ORSO_VERSION),
    }
    schema.update(Orso.__pydantic_model__.schema())
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
