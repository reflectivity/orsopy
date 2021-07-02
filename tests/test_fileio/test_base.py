"""
Tests for fileio.base module
"""

# author: Andrew R. McCluskey (arm61)

import unittest
from numpy.testing import assert_almost_equal, assert_equal
from orsopy import fileio


class TestHeader(unittest.TestCase):
    def test_value_scalar(self):
        c = fileio.ValueScalar(1., 'm')
        assert c.magnitude == 1.
        assert c.unit == 'm'

    def test_value_scale_list(self):
        c = fileio.ValueScalar([1, 2, 3], 'm')
        assert_equal(c.magnitude, [1, 2, 3])
        assert c.unit == 'm'

    def test_value_scalar_bad_unit(self):
        with self.assertRaises(ValueError):
            c = fileio.ValueScalar(1., 'Å')

    def test_value_scalar_to_yaml(self):
        c = fileio.ValueScalar(1., 'm')
        assert c.to_yaml() == 'magnitude: 1.0\nunit: m\n'

    def test_value_vector(self):
        c = fileio.ValueVector(1, 2, 3, 'm')
        assert c.x == 1
        assert c.y == 2
        assert c.z == 3
        assert c.unit == 'm'

    def test_value_vector_list(self):
        c = fileio.ValueVector([1, 2], [2, 3], [3, 4], 'm')
        assert_equal(c.x, [1, 2])
        assert_equal(c.y, [2, 3])
        assert_equal(c.z, [3, 4])
        assert c.unit == 'm'

    def test_value_vector_to_yaml(self):
        c = fileio.ValueVector(1., 2., 3., 'm')
        assert c.to_yaml() == 'x: 1.0\ny: 2.0\nz: 3.0\nunit: m\n'

    def test_value_range(self):
        c = fileio.ValueRange(1., 2., 'm')
        assert c.min == 1
        assert c.max == 2
        assert c.unit == 'm'

    def test_value_range_list(self):
        c = fileio.ValueRange([1, 2, 3], [2, 3, 4], 'm')
        assert_equal(c.min, [1, 2, 3])
        assert_equal(c.max, [2, 3, 4])
        assert c.unit == 'm'

    def test_value_range_bad_unit(self):
        with self.assertRaises(ValueError):
            c = fileio.ValueRange(1., 2., 'Å')

    def test_value_range_to_yaml(self):
        c = fileio.ValueRange(1., 2., 'm')
        assert c.to_yaml() == 'min: 1.0\nmax: 2.0\nunit: m\n'

    def test_comment(self):
        c = fileio.Comment('Hello World')
        assert c.comment == 'Hello World'

    def test_comment_to_yaml(self):
        c = fileio.Comment('Hello World')
        assert c.to_yaml() == 'comment: Hello World\n'

    def test_person(self):
        c = fileio.Person('Joe A. User', 'Ivy League University')
        assert c.name == 'Joe A. User'
        assert c.affiliation == 'Ivy League University'

    def test_person_email(self):
        c = fileio.Person('Joe A. User', 'Ivy League University',
                          'jauser@ivy.edu')
        assert c.name == 'Joe A. User'
        assert c.affiliation == 'Ivy League University'
        assert c.email == 'jauser@ivy.edu'

    def test_person_to_yaml(self):
        c = fileio.Person('Joe A. User', 'Ivy League University')
        assert c.to_yaml(
        ) == 'name: Joe A. User\naffiliation: Ivy League University\n'

    def test_person_no_affiliation(self):
        c = fileio.Person('Joe A. User', None)
        assert c.to_yaml() == 'name: Joe A. User\naffiliation: null\n'

    def test_person_email_to_yaml(self):
        c = fileio.Person('Joe A. User', 'Ivy League University',
                          'jauser@ivy.edu')
        assert c.to_yaml(
        ) == 'name: Joe A. User\naffiliation: Ivy League University\nemail: jauser@ivy.edu\n'

    def test_column(self):
        c = fileio.Column('q', '1/angstrom', 'qz vector')
        assert c.description == 'qz vector'
        assert c.quantity == 'q'
        assert c.unit == '1/angstrom'

    def test_column_bad_unit(self):
        with self.assertRaises(ValueError):
            c = fileio.Column('q', 'Å', 'qz vector')

    def test_column_repr(self):
        c = fileio.Column('q', '1/angstrom', 'qz vector')
        assert c.to_yaml(
        ) == 'quantity: q\nunit: 1/angstrom\ndescription: qz vector\n'
