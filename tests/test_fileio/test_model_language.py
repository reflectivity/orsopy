"""
Tests for fileio.model_language module
"""
# pylint: disable=R0201

import pathlib
import unittest

from datetime import datetime
from os.path import join as pjoin

import pytest

from orsopy.fileio import ComplexValue, Value
from orsopy.fileio import model_language as ml


class TestMaterial(unittest.TestCase):
    def test_empty(self):
        with self.assertRaises(ValueError):
            ml.Material()

    def test_values(self):
        m = ml.Material(formula="Fe2O3", mass_density={"magnitude": 7.0, "unit": "g/cm^3"})
        assert m.mass_density == Value(7.0, "g/cm^3")

    def test_default(self):
        defaults = ml.ModelParameters(
            mass_density_unit="g/cm^3",
            number_density_unit="1/nm^3",
            sld_unit="1/angstrom^2",
            magnetic_moment_unit="muB",
        )
        m = ml.Material(formula="Fe2O3", mass_density=7.0, number_density=0.15, sld=6.3e-6, magnetic_moment=3.4)
        m.resolve_defaults(defaults)

        assert m.mass_density == Value(7.0, "g/cm^3")
        assert m.number_density == Value(0.15, "1/nm^3")
        assert m.sld == Value(6.3e-6, "1/angstrom^2")
        assert m.magnetic_moment == Value(3.4, "muB")

        m = ml.Material(
            formula="Fe2O3",
            mass_density=Value(7.0),
            number_density=Value(0.15),
            sld=ComplexValue(6.3e-6),
            magnetic_moment=Value(3.4),
        )
        m.resolve_defaults(defaults)

    def test_density_lookup_elements(self):
        # no lookup case
        m = ml.Material(sld=Value(4e-6, "1/angstrom^3"))
        m.generate_density()
        # single element lookup case
        for element in ["Co", "Ni", "Si", "C"]:
            m = ml.Material(formula=element)
            m.generate_density()
            # repeat for caching
            m = ml.Material(formula=element)
            m.generate_density()
            assert m.number_density is not None
            assert m.comment.startswith("density from ORSO SLD db ID")
        # mixed element lookup case
        for element in ["Co0.8Cr0.2Fe0.1", "Ni3.4O5.4", "SiC4.3425"]:
            m = ml.Material(formula=element)
            m.generate_density()
            assert m.number_density is not None
            assert m.comment == "density from average element density"

    def test_sld(self):
        m = ml.Material(sld=ComplexValue(3.4e-6, -2e-6, "1/angstrom^2"))
        assert m.get_sld() == (3.4e-6 - 2e-6j)
        m = ml.Material(formula="Si", mass_density=Value(2.33, "g/cm^3"))
        self.assertAlmostEqual(m.get_sld().real, 2.07371e-6, 5)
        self.assertAlmostEqual(m.get_sld().imag, -0.00002e-6, 5)
        m = ml.Material(formula="Si", number_density=Value(0.04996026, "1/angstrom^3"))
        self.assertAlmostEqual(m.get_sld().real, 2.07371e-6, 5)
        self.assertAlmostEqual(m.get_sld().imag, -0.00002e-6, 5)
        m = ml.Material(formula="Si", number_density=Value(49.96026, "1/nm^3"))
        self.assertAlmostEqual(m.get_sld().real, 2.07371e-6, 5)
        self.assertAlmostEqual(m.get_sld().imag, -0.00002e-6, 5)
        m = ml.Material(formula="Si")
        assert m.get_sld() == (0.0j)

    def test_to_yaml(self):
        m = ml.Material(sld=ComplexValue(3.4e-6, -2e-6, "1/angstrom^2"))
        assert m.to_yaml() == "sld: {real: 3.4e-06, imag: -2.0e-06, unit: 1/angstrom^2}\n"
        m = ml.Material(
            formula="Si",
            mass_density=Value(2.33, "g/cm^3"),
            number_density=Value(0.04996026, "1/angstrom^3"),
            magnetic_moment=1.0,
        )
        assert m.to_yaml() == (
            "formula: Si\n"
            "mass_density: {magnitude: 2.33, unit: g/cm^3}\n"
            "number_density: {magnitude: 0.04996026, unit: 1/angstrom^3}\n"
            "magnetic_moment: 1.0\n"
        )


class TestComposit(unittest.TestCase):
    def test_wrong_value(self):
        with self.assertRaises(AttributeError):
            ml.Composit(composition="123")

    def test_resolution(self):
        materials = {"Si": ml.Material(formula="Si")}
        c = ml.Composit({"air": 0.3, "water": 0.3, "Si": 0.2, "Co": 0.1})
        c.resolve_names(materials)
        for key in ["air", "water", "Si", "Co"]:
            assert key in c._composition_materials

    def test_defaults(self):
        defaults = ml.ModelParameters(
            mass_density_unit="g/cm^3",
            number_density_unit="1/nm^3",
            sld_unit="1/angstrom^2",
            magnetic_moment_unit="muB",
        )
        materials = {
            "Si": ml.Material(formula="Fe2O3", mass_density=7.0, number_density=0.15, sld=6.3e-6, magnetic_moment=3.4)
        }
        c = ml.Composit({"Si": 1.0})
        c.resolve_names(materials)
        c.resolve_defaults(defaults)
        m = materials["Si"]
        assert m.mass_density == Value(7.0, "g/cm^3")
        assert m.number_density == Value(0.15, "1/nm^3")
        assert m.sld == Value(6.3e-6, "1/angstrom^2")
        assert m.magnetic_moment == Value(3.4, "muB")

    def test_density_lookup_elements(self):
        materials = {"Si": ml.Material(sld=Value(2.0e-6, "1/angstrom^2"))}
        c = ml.Composit({"Si": 0.5})
        c.resolve_names(materials)
        c.generate_density()

        self.assertAlmostEqual(c.get_sld(), 1.0e-6)

    def test_to_yaml(self):
        c = ml.Composit({"air": 0.3, "water": 0.3, "Si": 0.2, "Co": 0.1})
        assert c.to_yaml() == "composition:\n  air: 0.3\n  water: 0.3\n  Si: 0.2\n  Co: 0.1\n"


class TestLayer(unittest.TestCase):

    # TODO: This test case fails. Value does not enforce float, should be fixed.
    # def test_wrong_value(self):
    #     with self.assertRaises(ValueError):
    #         ml.Layer(thickness='abc')

    def test_empty(self):
        with self.assertRaises(ValueError):
            ml.Layer()

    def test_resolution(self):
        materials = {"Si": ml.Material(formula="Si")}
        lay = ml.Layer(composition={"air": 0.3, "water": 0.3, "Si": 0.2, "Co": 0.1})
        lay.resolve_names(materials)
        for key in ["air", "water", "Si", "Co"]:
            assert key in lay._composition_materials

        lay = ml.Layer(material="Si")
        lay.resolve_names(materials)
        assert lay.material is materials["Si"]

        lay = ml.Layer(material="air")
        lay.resolve_names(materials)
        assert lay.material is ml.SPECIAL_MATERIALS["air"]

        lay = ml.Layer(material=materials["Si"])
        lay.resolve_names(materials)
        assert lay.material is materials["Si"]

        c = ml.Composit({"Si": 1.0})
        lay = ml.Layer(material=c)
        lay.resolve_names(materials)
        assert lay.material is c

        lay = ml.Layer(material="Si")
        lay.resolve_names({})
        assert lay.material.formula == "Si"

    def test_defaults(self):
        defaults = ml.ModelParameters(
            mass_density_unit="g/cm^3",
            number_density_unit="1/nm^3",
            sld_unit="1/angstrom^2",
            magnetic_moment_unit="muB",
        )

        lay = ml.Layer(material=ml.Material(sld=2.0e-6))
        lay.resolve_defaults(defaults)

        assert lay.thickness == Value(0.0, defaults.length_unit)
        assert lay.roughness == defaults.roughness
        assert lay.material.sld.unit == defaults.sld_unit

        lay = ml.Layer(material=ml.Material(sld=Value(2.0e-6)), thickness=31.2, roughness=1.3)
        lay.resolve_defaults(defaults)

        assert lay.thickness == Value(31.2, defaults.length_unit)
        assert lay.roughness == Value(1.3, defaults.length_unit)
        assert lay.material.sld.unit == defaults.sld_unit

        lay = ml.Layer(
            material=ml.Material(sld=Value(2.0e-6, defaults.sld_unit)), thickness=Value(31.2), roughness=Value(1.3)
        )
        lay.resolve_defaults(defaults)

        assert lay.thickness == Value(31.2, defaults.length_unit)
        assert lay.roughness == Value(1.3, defaults.length_unit)

        lay = ml.Layer(composition={"Si": 1.0})
        lay.resolve_names({"Si": ml.Material(sld=2.0e-6)})
        lay.resolve_defaults(defaults)

        assert lay._composition_materials["Si"].sld.unit == defaults.sld_unit

    def test_material_mixing(self):
        lay = ml.Layer(composition={"Si": 1.0})
        lay.resolve_names({"Si": ml.Material(sld=Value(2.0e-6, unit="1/angstrom^2"))})
        lay.generate_material()

        assert isinstance(lay.material, ml.Material)
        assert lay.material.sld == ComplexValue(2.0e-6, 0.0, unit="1/angstrom^2")
