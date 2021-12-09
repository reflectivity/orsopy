"""
Module for compatibility with Python <3.8. Requires
the typing_extensions module to be installed.
"""

from typing import List, Tuple

from typing_extensions import Literal


def get_args(annotation):
    if annotation.__class__ is Literal.__class__:
        return annotation.__values__
    return getattr(annotation, "__args__", ())


def get_origin(annotation):
    atype = type(annotation)
    if hasattr(annotation, "__origin__"):
        orig = annotation.__origin__
        if orig is List:
            return list
        elif orig is Tuple:
            return tuple
        else:
            return orig
    elif annotation.__class__ is Literal.__class__:
        return Literal
    else:
        return atype
