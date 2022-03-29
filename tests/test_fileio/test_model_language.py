"""
Tests for fileio.model_language module
"""
# pylint: disable=R0201

import pathlib
import unittest

from datetime import datetime
from os.path import join as pjoin

import pytest

from orsopy.fileio import ComplexValue, Value, model_language


class TestMaterial(unittest.TestCase):
    """
    Testing the Material class.
    """

    def test_empty(self):
        """
        Creation of an object with a magnitude and unit.
        """
        with self.assertRaises(ValueError):
            model_language.Material()

    def test_values(self):
        m = model_language.Material(formula="Fe2O3", mass_density={"magnitude": 7.0, "unit": "g/cm^3"})
        assert m.mass_density == Value(7.0, "g/cm^3")

    def test_default(self):
        defaults = model_language.ModelParameters(
            mass_density_unit="g/cm^3",
            number_density_unit="1/nm^3",
            sld_unit="1/angstrom^2",
            magnetic_moment_unit="muB",
        )
        m = model_language.Material(
            formula="Fe2O3", mass_density=7.0, number_density=0.15, sld=6.3e-6, magnetic_moment=3.4
        )
        m.resolve_defaults(defaults)

        assert m.mass_density == Value(7.0, "g/cm^3")
        assert m.number_density == Value(0.15, "1/nm^3")
        assert m.sld == Value(6.3e-6, "1/angstrom^2")
        assert m.magnetic_moment == Value(3.4, "muB")

    def test_density_lookup_elements(self):
        # no lookup case
        m = model_language.Material(sld=Value(4e-6, "1/angstrom^3"))
        m.generate_density()
        # single element lookup case
        for element in ["Co", "Ni", "Si", "C"]:
            m = model_language.Material(formula=element)
            m.generate_density()
            assert m.number_density is not None
            assert m.comment.startswith("density from ORSO SLD db ID")
        # mixed element lookup case
        for element in ["Co0.8Cr0.2Fe0.1", "Ni3.4O5.4", "SiC4.3425"]:
            m = model_language.Material(formula=element)
            m.generate_density()
            assert m.number_density is not None
            assert m.comment == "density from average element density"

    def test_sld(self):
        m = model_language.Material(sld=ComplexValue(3.4e-6, -2e-6, "1/angstrom^2"))
        assert m.get_sld() == (3.4e-6 - 2e-6j)
        m = model_language.Material(formula="Si", mass_density=Value(2.33, "g/cm^3"))
        self.assertAlmostEqual(m.get_sld().real, 2.07371e-6, 5)
        self.assertAlmostEqual(m.get_sld().imag, -0.00002e-6, 5)
        m = model_language.Material(formula="Si", number_density=Value(0.04996026, "1/angstrom^3"))
        self.assertAlmostEqual(m.get_sld().real, 2.07371e-6, 5)
        self.assertAlmostEqual(m.get_sld().imag, -0.00002e-6, 5)
        m = model_language.Material(formula="Si", number_density=Value(49.96026, "1/nm^3"))
        self.assertAlmostEqual(m.get_sld().real, 2.07371e-6, 5)
        self.assertAlmostEqual(m.get_sld().imag, -0.00002e-6, 5)
        m = model_language.Material(formula="Si")
        assert m.get_sld() == (0.0j)
