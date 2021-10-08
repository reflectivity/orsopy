import os
if os.environ.get("GENERATE_SCHEMA", False):
    from pydantic.dataclasses import dataclass
else:
    from dataclasses import dataclass

from dataclasses import field, fields