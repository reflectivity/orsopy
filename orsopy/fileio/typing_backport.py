"""
Module for compatibility with Python <3.8. Requires
the typing_extensions module to be installed.
"""
from typing_extensions import Literal

def get_args(annotation):
    return getattr(annotation, '__args__', ())

def get_origin(annotation):
    atype = type(annotation)
    if hasattr(annotation, '__origin__'):
        orig = annotation.__origin__
        if orig is List:
            return list
        elif orig is Tuple:
            return tuple
        else:
            return orig
    else:
        return atype
