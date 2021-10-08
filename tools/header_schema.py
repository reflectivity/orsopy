"""
Generates the schema for an ORSO file.

Author: Brian Maranville (NIST)
"""
import os
os.environ["GENERATE_SCHEMA"] = "True"

def main():
    import orsopy
    from orsopy.fileio.orso import Orso

    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": "https://raw.githubusercontent.com/reflectivity/orsopy/v{version}/orsopy/fileio/schema/refl_header.schema.json".format(version=orsopy.__version__)
    }
    schema.update(Orso.__pydantic_model__.schema())
    print(schema)
    schema_path = os.path.join(os.path.dirname(orsopy.__file__), 'fileio', 'schema')
    import json

    open(os.path.join(schema_path, "refl_header.schema.json"), "wt").write(json.dumps(schema, indent=2))

    import yaml

    open(os.path.join(schema_path, "refl_header.schema.yaml"), "w").write(yaml.dump(schema))

if __name__ == '__main__':
    main()