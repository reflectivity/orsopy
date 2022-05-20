"""
Tests for fileio.base module
"""
# pylint: disable=R0201

import pathlib
import unittest

from datetime import datetime
from math import log, sqrt
from os.path import join as pjoin

import pint
import pytest

from numpy.testing import assert_equal

from orsopy.fileio import base, orso


class TestValue(unittest.TestCase):
    """
    Testing the Value class.
    """

    def test_single_value(self):
        """
        Creation of an object with a magnitude and unit.
        """
        value = base.Value(1.0, "m")
        assert value.magnitude == 1.0
        assert value.unit == "m"

    def test_list_warning(self):
        """
        Creation of an object with a a list of values and a unit.
        """
        with self.assertWarns(RuntimeWarning):
            value = base.Value([1, 2, 3], "m")
        assert_equal(value.magnitude, [1, 2, 3])
        assert value.unit == "m"

    def test_bad_unit(self):
        """
        Rejection of non-ASCII units.
        """
        with self.assertRaises(ValueError):
            _ = base.Value(1.0, "Å")

    def test_to_yaml(self):
        """
        Transform to yaml.
        """
        value = base.Value(1.0, "m")
        assert value.to_yaml() == "{magnitude: 1.0, unit: m}\n"

    def test_no_magnitude_to_yaml(self):
        """
        Transform to yaml with a non-optional ORSO item.
        """
        value = base.Value(None)
        assert value.to_yaml() == "{magnitude: null}\n"

    def test_user_data(self):
        value = base.Value(13.4, my_attr="hallo ORSO")
        assert value.user_data == {"my_attr": "hallo ORSO"}

    def test_unit_conversion(self):
        value = base.Value(1.0, "mm")
        assert value.as_unit("m") == 1.0e-3
        value = base.Value(1.0, "1/nm^3")
        assert value.as_unit("1/angstrom^3") == 1.0e-3

        with self.assertRaises(pint.DimensionalityError):
            value = base.Value(1.0, "1/nm^3")
            value.as_unit("m")


class TestComplexValue(unittest.TestCase):
    """
    Testing the Value class.
    """

    def test_single_value(self):
        """
        Creation of an object with a magnitude and unit.
        """
        value = base.ComplexValue(1.0, 2.0, "m")
        assert value.real == 1.0
        assert value.imag == 2.0
        assert value.unit == "m"

    def test_list(self):
        """
        Creation of an object with a a list of values and a unit.
        """
        value = base.ComplexValue([1, 2, 3], [4, 5, 6], "m")
        assert_equal(value.real, [1, 2, 3])
        assert_equal(value.imag, [4, 5, 6])
        assert value.unit == "m"

    def test_bad_unit(self):
        """
        Rejection of non-ASCII units.
        """
        with self.assertRaises(ValueError):
            _ = base.ComplexValue(1.0, 2.0, "Å")

    def test_to_yaml(self):
        """
        Transform to yaml.
        """
        value = base.ComplexValue(1.0, 2.0, "m")
        assert value.to_yaml() == "{real: 1.0, imag: 2.0, unit: m}\n"

    def test_no_magnitude_to_yaml(self):
        """
        Transform to yaml with a non-optional ORSO item.
        """
        value = base.ComplexValue(None)
        assert value.to_yaml() == "{real: null}\n"

    def test_unit_conversion(self):
        value = base.ComplexValue(1.0, 2.0, "mm")
        assert value.as_unit("m") == 1.0e-3 + 2.0e-3j
        value = base.ComplexValue(1.0, 2.0, "1/nm^3")
        assert value.as_unit("1/angstrom^3") == 1.0e-3 + 2.0e-3j

        with self.assertRaises(pint.DimensionalityError):
            value = base.ComplexValue(1.0, 2.0, "1/nm^3")
            value.as_unit("m")


class TestValueVector(unittest.TestCase):
    """
    Testing the ValueVector class
    """

    def test_single_value(self):
        """
        Creation of an object with three dimensions and unit.
        """
        value = base.ValueVector(1, 2, 3, "m")
        assert value.x == 1
        assert value.y == 2
        assert value.z == 3
        assert value.unit == "m"

    def test_list_warns(self):
        """
        Creation of an object with three dimensions of lists and unit.
        """
        with self.assertWarns(RuntimeWarning):
            value = base.ValueVector([1, 2], [2, 3], [3, 4], "m")
        assert_equal(value.x, [1, 2])
        assert_equal(value.y, [2, 3])
        assert_equal(value.z, [3, 4])
        assert value.unit == "m"

    def test_bad_unit(self):
        """
        Rejection of non-ASCII unit.
        """
        with self.assertRaises(ValueError):
            _ = base.ValueVector(1, 2, 3, "Å")

    def test_to_yaml(self):
        """
        Transform to yaml.
        """
        value = base.ValueVector(1.0, 2.0, 3.0, "m")
        assert value.to_yaml() == "x: 1.0\ny: 2.0\nz: 3.0\nunit: m\n"

    def test_two_dimensional_to_yaml(self):
        """
        Transform to yaml with only two dimensions.
        """
        value = base.ValueVector(1.0, 2.0, None, "m")
        assert value.to_yaml() == "x: 1.0\ny: 2.0\nz: null\nunit: m\n"

    def test_unit_conversion(self):
        value = base.ValueVector(1.0, 2.0, 3.0, "mm")
        assert value.as_unit("m") == (1.0e-3, 2.0e-3, 3.0e-3)
        value = base.ValueVector(1.0, 2.0, 3.0, "1/nm^3")
        assert value.as_unit("1/angstrom^3") == (1.0e-3, 2.0e-3, 3.0e-3)

        with self.assertRaises(pint.DimensionalityError):
            value = base.ValueVector(1.0, 2.0, 3.0, "1/m")
            value.as_unit("m")


class TestValueRange(unittest.TestCase):
    """
    Testing the ValueRange class
    """

    def test_single_value(self):
        """
        Creation of an object with a max, min and unit.
        """
        value = base.ValueRange(1.0, 2.0, "m")
        assert value.min == 1
        assert value.max == 2
        assert value.unit == "m"

    def test_list_warns(self):
        """
        Creation of an object of a list of max and list of min and a unit.
        """
        with self.assertWarns(RuntimeWarning):
            value = base.ValueRange([1, 2, 3], [2, 3, 4], "m")
        assert_equal(value.min, [1, 2, 3])
        assert_equal(value.max, [2, 3, 4])
        assert value.unit == "m"

    def test_bad_unit(self):
        """
        Rejection of non-ASCII unit.
        """
        with self.assertRaises(ValueError):
            _ = base.ValueRange(1.0, 2.0, "Å")

    def test_to_yaml(self):
        """
        Transform to yaml.
        """
        value = base.ValueRange(1.0, 2.0, "m")
        assert value.to_yaml() == "{min: 1.0, max: 2.0, unit: m}\n"

    def test_no_upper_to_yaml(self):
        """
        Transform to yaml with no max.
        """
        value = base.ValueRange(1.0, None)
        assert value.to_yaml() == "{min: 1.0, max: null}\n"

    def test_no_lower_to_yaml(self):
        """
        Transform to yaml with no min.
        """
        value = base.ValueRange(None, 1.0)
        assert value.to_yaml() == "{min: null, max: 1.0}\n"

    def test_unit_conversion(self):
        value = base.ValueRange(1.0, 2.0, "mm")
        assert value.as_unit("m") == (1.0e-3, 2.0e-3)
        value = base.ValueRange(1.0, 2.0, "1/nm^3")
        assert value.as_unit("1/angstrom^3") == (1.0e-3, 2.0e-3)

        with self.assertRaises(pint.DimensionalityError):
            value = base.ValueRange(1.0, 2.0, "1/m")
            value.as_unit("m")


class TestPerson(unittest.TestCase):
    """
    Testing the Person class
    """

    def test_creation(self):
        """
        Creation with no email.
        """
        value = base.Person("Joe A. User", "Ivy League University")
        assert value.name == "Joe A. User"
        assert value.affiliation == "Ivy League University"

    def test_creation_with_contact(self):
        """
        Creation with an email.
        """
        value = base.Person("Joe A. User", "Ivy League University", "jauser@ivy.edu")
        assert value.name == "Joe A. User"
        assert value.affiliation == "Ivy League University"
        assert value.contact == "jauser@ivy.edu"

    def test_creation_with_multiline(self):
        value = base.Person("Joe A. User", "\n".join(["Ivy League University", "Great Neutron Factory"]))
        assert value.name == "Joe A. User"
        assert value.affiliation == "\n".join(["Ivy League University", "Great Neutron Factory"])

    def test_to_yaml(self):
        """
        Transform to yaml with no email.
        """
        value = base.Person("Joe A. User", "Ivy League University")
        assert value.to_yaml() == "name: Joe A. User\naffiliation: Ivy League University\n"

    def test_no_affiliation_to_yaml(self):
        """
        Transform to yaml without affiliation.
        """
        value = base.Person("Joe A. User", None)
        assert value.to_yaml() == "name: Joe A. User\naffiliation: null\n"

    def test_no_name_to_yaml(self):
        """
        Transform to yaml without name.
        """
        value = base.Person(None, "A University")
        assert value.to_yaml() == "name: null\naffiliation: A University\n"

    def test_email_to_yaml(self):
        """
        Transform to yaml with an email.
        """
        value = base.Person("Joe A. User", "Ivy League University", "jauser@ivy.edu")
        assert (
            value.to_yaml() == "name: Joe A. User\naffiliation: Ivy League University" + "\ncontact: jauser@ivy.edu\n"
        )


class TestColumn(unittest.TestCase):
    """
    Testing the Column class
    """

    def test_creation(self):
        """
        Creation of a column.
        """
        value = base.Column("q", "1/angstrom", "qz vector")
        assert value.dimension == "qz vector"
        assert value.name == "q"
        assert value.unit == "1/angstrom"

    def test_bad_unit(self):
        """
        Rejection of non-ASCII unit.
        """
        with self.assertRaises(ValueError):
            _ = base.Column("q", "Å", "qz vector")

    def test_to_yaml(self):
        """
        Transformation to yaml.
        """
        value = base.Column("q", "1/angstrom", "qz vector")
        assert value.to_yaml() == "{name: q, unit: 1/angstrom, dimension: qz vector}\n"

    def test_no_description_to_yaml(self):
        """
        Transformation to yaml.
        """
        value = base.Column("q", "1/angstrom")
        assert value.to_yaml() == "{name: q, unit: 1/angstrom}\n"


class TestErrorColumn(unittest.TestCase):
    """
    Testing the Column class
    """

    def test_creation(self):
        """
        Creation of a column.
        """
        value = base.ErrorColumn("q", "uncertainty", "FWHM", "triangular")
        assert value.error_of == "q"
        assert value.error_type == "uncertainty"
        assert value.distribution == "triangular"
        assert value.value_is == "FWHM"
        value = base.ErrorColumn("q", "resolution", "sigma", "gaussian")
        assert value.error_of == "q"
        assert value.error_type == "resolution"
        assert value.distribution == "gaussian"
        assert value.value_is == "sigma"
        assert value.name == "sq"

    def test_bad_type(self):
        """
        Rejection of non-ASCII unit.
        """
        with self.assertWarns(RuntimeWarning):
            _ = base.ErrorColumn("q", "nm")

    def test_bad_distribution(self):
        """
        Rejection of non-ASCII unit.
        """
        with self.assertWarns(RuntimeWarning):
            _ = base.ErrorColumn("q", "uncertainty", "FWHM", "undefined")
        with self.assertWarns(RuntimeWarning):
            _ = base.ErrorColumn("q", "uncertainty", "HWHM", "triangular")
        with self.assertWarns(RuntimeWarning):
            _ = base.ErrorColumn("q", "uncertainty", "wrong")

    def test_to_yaml(self):
        """
        Transformation to yaml.
        """
        value = base.ErrorColumn("q", "uncertainty", "FWHM", "triangular")
        assert value.to_yaml() == "{error_of: q, error_type: uncertainty, value_is: FWHM, distribution: triangular}\n"

    def test_minimal_to_yaml(self):
        """
        Transformation to yaml.
        """
        value = base.ErrorColumn("q")
        assert value.to_yaml() == "{error_of: q}\n"

    def test_sigma_conversion(self):
        with self.subTest("gauss"):
            value = base.ErrorColumn("q", "uncertainty", "FWHM", "gaussian")
            self.assertEqual(value.to_sigma, 1.0 / (2.0 * sqrt(2.0 * log(2.0))))
        with self.subTest("uniform"):
            value = base.ErrorColumn("q", "uncertainty", "FWHM", "uniform")
            self.assertEqual(value.to_sigma, 1.0 / sqrt(12.0))
        with self.subTest("triangular"):
            value = base.ErrorColumn("q", "uncertainty", "FWHM", "triangular")
            self.assertEqual(value.to_sigma, 1.0 / sqrt(6.0))
        with self.subTest("lorentizan"):
            value = base.ErrorColumn("q", "uncertainty", "FWHM", "lorentzian")
            with self.assertRaises(ValueError):
                value.to_sigma


class TestFile(unittest.TestCase):
    """
    Testing the File class.
    """

    def test_creation_for_nonexistent_file(self):
        """
        Creation of a file that does not exist.
        """
        value = base.File("not_a_file.txt", datetime(2021, 7, 12, 14, 4, 20))
        assert value.file == "not_a_file.txt"
        assert value.timestamp == datetime(2021, 7, 12, 14, 4, 20)

    def test_to_yaml_for_nonexistent_file(self):
        """
        Transformation to yaml of a file that does not exist.
        """
        value = base.File("not_a_file.txt", datetime(2021, 7, 12, 14, 4, 20))
        assert value.to_yaml() == "file: not_a_file.txt\ntimestamp: " + "2021-07-12T14:04:20\n"

    def test_creation_for_existing_file(self):
        """
        Creation for a file that does exist with a given modified date.
        """
        fname = pathlib.Path("README.rst")
        value = base.File(str(fname.absolute()), datetime.fromtimestamp(fname.stat().st_mtime))
        assert value.file == str(pathlib.Path().resolve().joinpath("README.rst"))
        assert value.timestamp == datetime.fromtimestamp(fname.stat().st_mtime)

    def test_to_yaml_for_existing_file(self):
        """
        Transformation to yaml a file that does exist with a given modified
        date.
        """
        fname = pathlib.Path("README.rst")
        value = base.File(str(fname.absolute()), datetime.fromtimestamp(fname.stat().st_mtime))
        assert (
            value.to_yaml()
            == f'file: {str(pathlib.Path().resolve().joinpath("README.rst"))}\n'
            + "timestamp: "
            + f"{datetime.fromtimestamp(fname.stat().st_mtime).isoformat()}\n"
        )

    def test_creation_for_existing_file_no_mod_time(self):
        """
        Transformation to yaml a file that does exist without a given
        modified date.
        """
        fname = pathlib.Path("AUTHORS.rst")
        value = base.File(str(fname.absolute()), None)
        assert value.file == str(pathlib.Path().resolve().joinpath("AUTHORS.rst"))
        assert value.timestamp == datetime.fromtimestamp(fname.stat().st_mtime)

    def test_to_yaml_for_existing_file_no_mod_time(self):
        """
        Transformation to yaml a file that does exist without a given
        modified date.
        """
        fname = pathlib.Path("AUTHORS.rst")
        value = base.File(str(fname.absolute()), None)
        assert (
            value.to_yaml()
            == "file: "
            + f'{str(pathlib.Path().resolve().joinpath("AUTHORS.rst"))}\n'
            + "timestamp: "
            + f"{datetime.fromtimestamp(fname.stat().st_mtime).isoformat()}\n"
        )


def test_not_orso():
    with pytest.raises(base.NotOrsoCompatibleFileError, match="First line does not appea"):
        orso.load_orso(pjoin("tests", "not_orso.ort"))
