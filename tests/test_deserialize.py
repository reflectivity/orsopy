import yaml

# block loading of datetime objects, for validation only (json schema can not contain datetime objects, only formatted string)
def timestamp_constructor(loader, node):
    return str(node.value)

class StringDatetimeLoader(yaml.Loader):
    pass
    
StringDatetimeLoader.add_constructor(u'tag:yaml.org,2002:timestamp', timestamp_constructor)
        

def read_header(filename, parse_datetime=True):
    with open(filename, 'rt') as datafile:
        header_lines = [line[2:] for line in datafile if line.startswith("# ")]
        header = ''.join(header_lines)
    
    Loader = yaml.Loader if parse_datetime else StringDatetimeLoader
    return yaml.load(header, Loader=Loader)
    

header = read_header('test_example.ort')

from header_schema_deserialize import *


