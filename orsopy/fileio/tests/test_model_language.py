"""
Tests for fileio.model_language module
"""
# pylint: disable=R0201

import unittest

from datetime import datetime
from os.path import join as pjoin

import pytest

from orsopy.fileio import ComplexValue, Value
from orsopy.fileio import model_language as ml


class TestMaterial(unittest.TestCase):
    def test_empty(self):
        with self.assertRaises(ValueError):
            mat = ml.Material()
            mat.resolve_defaults({})

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
            assert m.comment == "density from average element density from ORSO SLD db"

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
        with pytest.warns(RuntimeWarning):
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
            lay = ml.Layer()
            lay.resolve_names({})

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


class TestSubStack(unittest.TestCase):
    def test_empty(self):
        empty = ml.SubStack.empty()
        with self.assertRaises(ValueError):
            empty.resolve_names({})

    def test_resolution(self):
        s = ml.SubStack(stack="air | b 13 |c|d")
        resolvable_items = {
            "d": ml.Layer(material=ml.Material(sld=Value(2e-6, "1/angstrom^2"))),
            "b": ml.Material(formula="Co"),
            "c": ml.Composit({"b": 1.0}),
        }
        s.resolve_names(resolvable_items)
        assert len(s.sequence) == 4
        assert s.sequence[0] == ml.Layer(thickness=0.0, material=ml.SPECIAL_MATERIALS["air"])
        assert s.sequence[1] == ml.Layer(thickness=13.0, material=ml.Material(formula="Co"))
        assert s.sequence[2] == ml.Layer(thickness=0.0, material=ml.Composit({"b": 1.0}))
        assert s.sequence[3] == resolvable_items["d"]

        s = ml.SubStack(stack="air | 2( b 13 | c 5)|d")
        s.resolve_names(resolvable_items)
        assert len(s.sequence) == 3
        assert s.sequence[0] == ml.Layer(thickness=0.0, material=ml.SPECIAL_MATERIALS["air"])
        assert s.sequence[1] == ml.SubStack(
            repetitions=2,
            stack="b 13 | c 5",
            sequence=[
                ml.Layer(thickness=13.0, material=ml.Material(formula="Co")),
                ml.Layer(thickness=5.0, material=ml.Composit(composition={"b": 1.0})),
            ],
        )
        assert s.sequence[2] == resolvable_items["d"]

        s = ml.SubStack(sequence=[ml.Layer(thickness=13.0, material="b"), ml.Layer(thickness=5.0, material="c")])
        s.resolve_names(resolvable_items)
        assert s.sequence == [
            ml.Layer(thickness=13.0, material=ml.Material(formula="Co")),
            ml.Layer(thickness=5.0, material=ml.Composit(composition={"b": 1.0})),
        ]

    def test_defaults(self):
        defaults = ml.ModelParameters(
            mass_density_unit="g/cm^3",
            number_density_unit="1/nm^3",
            sld_unit="1/angstrom^2",
            magnetic_moment_unit="muB",
        )

        s = ml.SubStack(sequence=[ml.Layer(thickness=13.0, material=ml.Material(formula="Co"))])
        s.resolve_defaults(defaults)
        assert s.sequence[0].thickness == Value(13.0, defaults.length_unit)

    def test_resolve_layers(self):
        resolvable_items = {
            "d": ml.Layer(material=ml.Material(sld=Value(2e-6, "1/angstrom^2"))),
            "b": ml.Material(formula="Co"),
            "c": ml.Composit({"b": 1.0}),
            "e": ml.Layer(composition={"b": 1.0}),
        }
        s = ml.SubStack(stack="air | 2( b 13 | c 5)|d|e")
        s.resolve_names(resolvable_items)
        lays = s.resolve_to_layers()
        assert len(lays) == 7


class TestSampleModel(unittest.TestCase):
    def test_resolvable_items(self):
        sub_stacks = {"a": ml.SubStack(stack="b")}
        layers = {"b": ml.Layer(thickness=13.4, material="c")}
        materials = {"c": ml.Material(sld=13.4)}
        composits = {"d": ml.Composit({"c": 1.0})}
        sm = ml.SampleModel(
            stack="c|a|c", sub_stacks=sub_stacks, layers=layers, materials=materials, composits=composits
        )
        res = sm.resolvable_items
        assert list(res.keys()) == ["a", "b", "c", "d"]
        assert list(res.values()) == [sub_stacks["a"], layers["b"], materials["c"], composits["d"]]

    def test_duplicate_name(self):
        with pytest.warns(UserWarning):
            ml.SampleModel(
                stack="c|a|c",
                layers={"a": ml.Layer(thickness=13.4, material="c")},
                materials={"a": ml.Material(sld=13.4)},
            )

    def test_resolve_stack(self):
        defaults = ml.ModelParameters(
            mass_density_unit="g/cm^3",
            number_density_unit="1/nm^3",
            sld_unit="1/angstrom^2",
            magnetic_moment_unit="muB",
            length_unit="nm",
            roughness=Value(0.3, "nm"),
        )

        sub_stacks = {"a": ml.SubStack(stack="b")}
        layers = {"b": ml.Layer(thickness=13.4, material="c")}
        materials = {"c": ml.Material(sld=13.4)}
        composits = {"d": ml.Composit({"c": 1.0})}
        sm = ml.SampleModel(
            stack="c|2(a|c 15)|d 14|c",
            sub_stacks=sub_stacks,
            layers=layers,
            materials=materials,
            composits=composits,
            globals=defaults,
        )
        stack = sm.resolve_stack()
        subs = ml.SubStack(repetitions=2, stack="a|c 15")
        subs.resolve_names({"a": sub_stacks["a"], "c": materials["c"]})
        subs.resolve_defaults(defaults)
        assert len(stack) == 4
        assert stack[0] == ml.Layer(
            thickness=ml.Value(0.0, "nm"), roughness=defaults.roughness, material=materials["c"]
        )
        assert stack[1] == subs
        assert stack[2] == ml.Layer(
            thickness=ml.Value(14.0, "nm"), roughness=defaults.roughness, material=composits["d"]
        )
        assert stack[3] == ml.Layer(
            thickness=ml.Value(0.0, "nm"), roughness=defaults.roughness, material=materials["c"]
        )
        sm = ml.SampleModel("Si")
        stack = sm.resolve_stack()
        assert len(stack) == 1
        assert stack[0] == ml.Layer(
            ml.Value(0.0, "nm"), roughness=defaults.roughness, material=ml.Material(formula="Si")
        )

    def test_resolve_to_layers(self):
        defaults = ml.ModelParameters(
            mass_density_unit="g/cm^3",
            number_density_unit="1/nm^3",
            sld_unit="1/angstrom^2",
            magnetic_moment_unit="muB",
            length_unit="nm",
            roughness=Value(0.3, "nm"),
        )

        sub_stacks = {"a": ml.SubStack(stack="b")}
        layers = {"b": ml.Layer(thickness=13.4, material="c"), "b2": ml.Layer(thickness=2.0, composition={"c": 1.0})}
        materials = {"c": ml.Material(sld=13.4)}
        composits = {"d": ml.Composit({"c": 1.0})}
        sm = ml.SampleModel(
            stack="c|2(a|c 15)|b|b2|d 14|Si",
            sub_stacks=sub_stacks,
            layers=layers,
            materials=materials,
            composits=composits,
            globals=defaults,
        )
        mSi = ml.Material(formula="Si")
        mSi.generate_density()
        ls = sm.resolve_to_layers()
        assert len(ls) == 9
        assert ls[0] == ml.Layer(thickness=ml.Value(0.0, "nm"), roughness=defaults.roughness, material=materials["c"])
        assert ls[1] == ls[3]
        assert ls[2] == ls[4]
        assert ls[5] == ml.Layer(thickness=ml.Value(13.4, "nm"), roughness=defaults.roughness, material=materials["c"])
        assert ls[6] == ml.Layer(
            thickness=ml.Value(2.0, "nm"),
            roughness=defaults.roughness,
            material=ml.Material(sld=ComplexValue(13.4, 0.0, "1/angstrom^2"), comment="composition material: 1.0xc"),
            composition={"c": 1.0},
        )
        assert ls[7] == ml.Layer(thickness=ml.Value(14.0, "nm"), roughness=defaults.roughness, material=composits["d"])
        assert ls[8] == ml.Layer(thickness=Value(0.0, "nm"), roughness=defaults.roughness, material=mSi)
