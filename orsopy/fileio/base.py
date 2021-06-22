"""
Implementation of the base classes for the ORSO header.
"""

# author: Andrew R. McCluskey (arm61)

import yaml


def noop(self, *args, **kw):
    pass


yaml.emitter.Emitter.process_tag = noop


def _repr(class_to_represent):
    """
    The representation object for all the Header sub-classes. This returns a
    string in a yaml format which will be ORSO compatible.

    Args:
        class_to_represent (:py:class:`object`): The class to be represented.

    Returns:
        (:py:attr:`str`): A string representation.
    """
    cleaned_data = dict(
        (k, v) for (k, v) in class_to_represent.__dict__.items(
        ) if v is not None
    )
    return yaml.dump(cleaned_data, sort_keys=False)


class Header:
    """
    The super class for all of the __repr__ items in the orso module
    """

    def __repr__(self):
        """
        The string representation for the Header class objects.
        """
        return _repr(self)


class MagnetizationVector(Header):
    """
    A descriptor for the magnetization vector.
    """
    def __init__(self):
        pass


class Unit(Header):
    """
    A unit for a value.

    Args:
        unit (:py:attr:`str`): The unit.
    """
    def __init__(self, unit):
        _check_unit(unit)
        self.unit = unit


class ValueScalar(Unit):
    """
    A single value with an unit.

    Args:
        magnitude (:py:attr:`float`): The value.
        unit (:py:attr:`str`, optional): The unit. Optional,
            defaults to :code:`'dimensionless'`.
    """

    def __init__(self, magnitude, unit="dimensionless"):
        super().__init__(unit)
        self.magnitude = magnitude


class ValueVector(ValueScalar):
    """
    A single value with an unit and a direction.

    Args:
        magnitude (:py:attr:`float`): The value.
        direction (:py:attr:`tuple`): A description of the vector direction.
        unit (:py:attr:`str`, optional): The unit. Optional,
            defaults to :code:`'dimensionless'`.
    """

    def __init__(self, magnitude, direction, unit="dimensionless"):
        super().__init__(magnitude, unit=unit)
        self.direction = direction


class ValueRange(Unit):
    """
    A range of value with a min, a max, and a unit.

    Args:
        min (:py:attr:`float`): The minimum value.
        max (:py:attr:`float`): The maximum value.
        unit (:py:attr:`str`, optional): The unit. Optional,
            defaults to :code:`'dimensionless'`.
    """

    def __init__(self, min, max, unit="dimensionless"):
        super().__init__(unit)
        self.min = min
        self.max = max


class Comment(Header):
    """
    A comment.

    Args:
        comment (:py:attr:`str`): The comment.
    """

    def __init__(self, comment):
        self.comment = comment


class Person(Header):
    """
    Information about a person.

    Args:
        name (:py:attr:`str`): A name for the person
        affiliation (:py:attr:`str`): An affiliation for the person
        email (:py:attr:`str`, optional): A contact email for the person.
            Defaults to :py:attr:`None`.
    """

    def __init__(self, name, affiliation, email=None):
        self.name = name
        self.affiliation = affiliation
        self.email = email


class Column(Header):
    """
    Information on a data column.

    Args:
        quantity (:py:attr:`str`): The name of the column.
        unit (:py:attr:`str`, optional): The unit. Optional, defaults
            to :code:`'dimensionless'`.
        description (:py:attr:`str`, optional): A description of the column.
            Optional, defaults to :code:`'None'`.
    """

    def __init__(self, quantity, unit="dimensionless", description=None):
        _check_unit(unit)
        self.quantity = quantity
        self.unit = unit
        self.description = description


def _is_ascii(s):
    """
    Checks if the input is ASCII.

    Args:
        s (:py:attr:`str`): Input to check

    Returns:
        (:py:attr:`bool`): True if value is ASCII
    """
    return all(ord(c) < 128 for c in s)


def _check_unit(unit):
    """
    Check if the unit is valid, in future this could include recommendations.

    Args:
        unit (:py:attr:`str`): Unit to be checked.
    """
    if not _is_ascii(unit):
        raise ValueError("The unit must be in ASCII text.")
