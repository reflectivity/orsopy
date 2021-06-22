"""
Tests for fileio.base module
"""

# author: Andrew R. McCluskey (arm61)

from orsopy.fileio.base import ValueVector
import unittest
from numpy.testing import assert_almost_equal, assert_equal
from orsopy import fileio


class TestHeader(unittest.TestCase):
    def test_value_scalar(self):
        c = fileio.ValueScalar(1., 'm')
        assert_almost_equal(c.magnitude, 1)
        assert_equal(c.unit, 'm')

    def test_value_scalar_bad_unit(self):
        with self.assertRaises(ValueError):
            c = fileio.ValueScalar(1., 'Å')

    def test_value_scalar_repr(self):
        c = fileio.ValueScalar(1., 'm')
        assert_equal(c.__repr__(), 'magnitude: 1.0\nunit: m\n')

    def test_value_vector(self):
        c = fileio.ValueVector(1., (1, 2, 3), 'm')
        assert_almost_equal(c.magnitude, 1)
        assert_equal(c.direction, (1, 2, 3))
        assert_equal(c.unit, 'm')

    def test_value_vector_repr(self):
        c = fileio.ValueVector(1., (1, 2, 3), 'm')
        assert_equal(
            c.__repr__(), 'magnitude: 1.0\nunit: m\ndirection:\n- 1\n- 2\n- 3\n')

    def test_value_range(self):
        c = fileio.ValueRange(1., 2., 'm')
        assert_almost_equal(c.min, 1)
        assert_almost_equal(c.max, 2)
        assert_equal(c.unit, 'm')

    def test_value_range_bad_unit(self):
        with self.assertRaises(ValueError):
            c = fileio.ValueRange(1., 2., 'Å')

    def test_value_range_repr(self):
        c = fileio.ValueRange(1., 2., 'm')
        assert_equal(c.__repr__(), 'min: 1.0\nmax: 2.0\nunit: m\n')

    def test_comment(self):
        c = fileio.Comment('Hello World')
        assert_equal(c.comment, 'Hello World')

    def test_comment_repr(self):
        c = fileio.Comment('Hello World')
        assert_equal(c.__repr__(), 'comment: Hello World\n')

    def test_person(self):
        c = fileio.Person('Joe A. User', 'Ivy League University')
        assert_equal(c.name, 'Joe A. User')
        assert_equal(c.affiliation, 'Ivy League University')

    def test_person_email(self):
        c = fileio.Person('Joe A. User', 'Ivy League University', 'jauser@ivy.edu')
        assert_equal(c.name, 'Joe A. User')
        assert_equal(c.affiliation, 'Ivy League University')
        assert_equal(c.email, 'jauser@ivy.edu')

    def test_person_repr(self):
        c = fileio.Person('Joe A. User', 'Ivy League University')
        assert_equal(c.__repr__(), 'name: Joe A. User\naffiliation: Ivy League University\n')
    
    def test_person_email_repr(self):
        c = fileio.Person(
            'Joe A. User', 'Ivy League University', 'jauser@ivy.edu')
        assert_equal(
            c.__repr__(), 'name: Joe A. User\naffiliation: Ivy League University\nemail: jauser@ivy.edu\n')

    def test_column(self):
        c = fileio.Column('q', '1/angstrom', 'qz vector')
        assert_equal(c.description, 'qz vector')
        assert_equal(c.quantity, 'q')
        assert_equal(c.unit, '1/angstrom')

    def test_column_bad_unit(self):
        with self.assertRaises(ValueError):
            c = fileio.Column('q', 'Å', 'qz vector')

    def test_column_repr(self):
        c = fileio.Column('q', '1/angstrom', 'qz vector')
        assert_equal(c.__repr__(), 'quantity: q\nunit: 1/angstrom\ndescription: qz vector\n')

    def test__is_ascii(self):
        assert_equal(fileio.base._is_ascii('Some text'), True)

    def test__is_ascii_false(self):
        assert_equal(fileio.base._is_ascii('Å'), False)
    
    def test__check_unit(self):
        with self.assertRaises(ValueError):
            fileio.base._check_unit('Å')
