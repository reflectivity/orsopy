"""
Tests for fileio.base module
"""

# author: Andrew R. McCluskey (arm61)
# pylint: disable=R0201

import unittest
from numpy.testing import assert_equal
from orsopy import fileio


class TestValueScalar(unittest.TestCase):
    """
    Testing the ValueScalar class.
    """
    def test_single_value(self):
        """
        Creation of an object with a magnitude and unit.
        """
        value = fileio.ValueScalar(1., 'm')
        assert value.magnitude == 1.
        assert value.unit == 'm'

    def test_list(self):
        """
        Creation of an object with a a list of values and a unit.
        """
        value = fileio.ValueScalar([1, 2, 3], 'm')
        assert_equal(value.magnitude, [1, 2, 3])
        assert value.unit == 'm'

    def test_bad_unit(self):
        """
        Rejection of non-ASCII units.
        """
        with self.assertRaises(ValueError):
            _ = fileio.ValueScalar(1., 'Å')

    def test_to_yaml(self):
        """
        Transform to yaml.
        """
        value = fileio.ValueScalar(1., 'm')
        assert value.to_yaml() == 'magnitude: 1.0\nunit: m\n'

    def test_no_magnitude_to_yaml(self):
        """
        Transform to yaml with a non-optional ORSO item.
        """
        value = fileio.ValueScalar(None)
        assert value.to_yaml() == 'magnitude: null\n'


class TestValueVector(unittest.TestCase):
    """
    Testing the ValueVector class
    """
    def test_single_value(self):
        """
        Creation of an object with three dimensions and unit.
        """
        value = fileio.ValueVector(1, 2, 3, 'm')
        assert value.x == 1
        assert value.y == 2
        assert value.z == 3
        assert value.unit == 'm'

    def test_list(self):
        """
        Creation of an object with three dimensions of lists and unit.
        """
        value = fileio.ValueVector([1, 2], [2, 3], [3, 4], 'm')
        assert_equal(value.x, [1, 2])
        assert_equal(value.y, [2, 3])
        assert_equal(value.z, [3, 4])
        assert value.unit == 'm'

    def test_bad_unit(self):
        """
        Rejection of non-ASCII unit.
        """
        with self.assertRaises(ValueError):
            _ = fileio.ValueVector(1, 2, 3, 'Å')

    def test_to_yaml(self):
        """
        Transform to yaml.
        """
        value = fileio.ValueVector(1., 2., 3., 'm')
        assert value.to_yaml() == 'x: 1.0\ny: 2.0\nz: 3.0\nunit: m\n'

    def test_two_dimensional_to_yaml(self):
        """
        Transform to yaml with only two dimensions.
        """
        value = fileio.ValueVector(1., 2., None, 'm')
        assert value.to_yaml() == 'x: 1.0\ny: 2.0\nz: null\nunit: m\n'


class TestValueRange(unittest.TestCase):
    """
    Testing the ValueRange class
    """
    def test_single_value(self):
        """
        Creation of an object with a max, min and unit.
        """
        value = fileio.ValueRange(1., 2., 'm')
        assert value.min == 1
        assert value.max == 2
        assert value.unit == 'm'

    def test_list(self):
        """
        Creation of an object of a list of max and list of min and a unit.
        """
        value = fileio.ValueRange([1, 2, 3], [2, 3, 4], 'm')
        assert_equal(value.min, [1, 2, 3])
        assert_equal(value.max, [2, 3, 4])
        assert value.unit == 'm'

    def test_bad_unit(self):
        """
        Rejection of non-ASCII unit.
        """
        with self.assertRaises(ValueError):
            _ = fileio.ValueRange(1., 2., 'Å')

    def test_to_yaml(self):
        """
        Transform to yaml.
        """
        value = fileio.ValueRange(1., 2., 'm')
        assert value.to_yaml() == 'min: 1.0\nmax: 2.0\nunit: m\n'

    def test_no_upper_to_yaml(self):
        """
        Transform to yaml with no max.
        """
        value = fileio.ValueRange(1., None)
        assert value.to_yaml() == 'min: 1.0\nmax: null\n'

    def test_no_lower_to_yaml(self):
        """
        Transform to yaml with no min.
        """
        value = fileio.ValueRange(None, 1.)
        assert value.to_yaml() == 'min: null\nmax: 1.0\n'


class TestComment(unittest.TestCase):
    """
    Testing the Comment class
    """
    def test_creation(self):
        """
        Creation of a comment.
        """
        value = fileio.Comment('Hello World')
        assert value.comment == 'Hello World'

    def test_to_yaml(self):
        """
        Transform to yaml.
        """
        value = fileio.Comment('Hello World')
        assert value.to_yaml() == 'comment: Hello World\n'

    def test_no_comment_to_yaml(self):
        """
        Transform to yaml with None.
        """
        value = fileio.Comment(None)
        assert value.to_yaml() == 'comment: null\n'


class TestPerson(unittest.TestCase):
    """
    Testing the Person class
    """
    def test_creation(self):
        """
        Creation with no email.
        """
        value = fileio.Person('Joe A. User', 'Ivy League University')
        assert value.name == 'Joe A. User'
        assert value.affiliation == 'Ivy League University'

    def test_creation_with_email(self):
        """
        Creation with an email.
        """
        value = fileio.Person('Joe A. User', 'Ivy League University',
                              'jauser@ivy.edu')
        assert value.name == 'Joe A. User'
        assert value.affiliation == 'Ivy League University'
        assert value.email == 'jauser@ivy.edu'

    def test_to_yaml(self):
        """
        Transform to yaml with no email.
        """
        value = fileio.Person('Joe A. User', 'Ivy League University')
        assert value.to_yaml(
        ) == 'name: Joe A. User\naffiliation: Ivy League University\n'

    def test_no_affiliation_to_yaml(self):
        """
        Transform to yaml without affiliation.
        """
        value = fileio.Person('Joe A. User', None)
        assert value.to_yaml() == 'name: Joe A. User\naffiliation: null\n'

    def test_no_name_to_yaml(self):
        """
        Transform to yaml without name.
        """
        value = fileio.Person(None, 'A University')
        assert value.to_yaml() == 'name: null\naffiliation: A University\n'

    def test_email_to_yaml(self):
        """
        Transform to yaml with an email.
        """
        value = fileio.Person('Joe A. User', 'Ivy League University',
                              'jauser@ivy.edu')
        assert value.to_yaml(
        ) == 'name: Joe A. User\naffiliation: Ivy League University'\
            + '\nemail: jauser@ivy.edu\n'


class TestColumn(unittest.TestCase):
    """
    Testing the Column class
    """
    def test_creation(self):
        """
        Creation of a column.
        """
        value = fileio.Column('q', '1/angstrom', 'qz vector')
        assert value.description == 'qz vector'
        assert value.quantity == 'q'
        assert value.unit == '1/angstrom'

    def test_bad_unit(self):
        """
        Rejection of non-ASCII unit.
        """
        with self.assertRaises(ValueError):
            _ = fileio.Column('q', 'Å', 'qz vector')

    def test_to_yaml(self):
        """
        Transformation to yaml.
        """
        value = fileio.Column('q', '1/angstrom', 'qz vector')
        assert value.to_yaml(
        ) == 'quantity: q\nunit: 1/angstrom\ndescription: qz vector\n'

    def test_no_description_to_yaml(self):
        """
        Transformation to yaml.
        """
        value = fileio.Column('q', '1/angstrom')
        assert value.to_yaml() == 'quantity: q\nunit: 1/angstrom\n'
