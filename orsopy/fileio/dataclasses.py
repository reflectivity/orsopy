import os
from typing import Dict, Any

if os.environ.get("GENERATE_SCHEMA", False) == "True":
    import functools
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
                    # special handling for columns: allow additional Column
                    # items after 4 predefined spots.
                    if prop == 'columns':
                        value['anyOf'][-1]['additionalItems'] = {"$ref": "#/definitions/Column"}
                    else:
                        value['anyOf'].append({'type': 'null'})
                # only one $ref e.g. from other model
                elif '$ref' in value:
                    value['anyOf'] = [{'$ref': value.pop('$ref')}]

    dataclass = functools.partial(_dataclass, config=Config)
else:
    from dataclasses import dataclass

from dataclasses import field, fields