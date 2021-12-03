import unittest

import numpy as np

from orsopy.slddb import element_table


class TestFormula(unittest.TestCase):
    def test_load_symbol(self):
        element_table.get_element("O")
        element_table.get_element("Cr")
        element_table.get_element("Gd")
        element_table.get_element("Pb")
        element_table.get_element("U")
        element_table.get_element("Pu")
        element_table.get_element("D")

    def test_load_Z(self):
        element_table.get_element(16)
        element_table.get_element(8)
        element_table.get_element(32)

    def test_load_isotope(self):
        element_table.get_element("O[16]")
        element_table.get_element("B[10]")
        element_table.get_element("D")
        element_table.get_element("H[2]")

    def test_equality(self):
        e1 = element_table.get_element("O")
        e2 = element_table.get_element("O")
        e3 = element_table.get_element(8)
        self.assertEqual(e1, e2)
        self.assertEqual(e1, e3)
        self.assertNotEqual(e1, 13)

    def test_hash(self):
        d = {element_table.get_element("O"): "O"}
        d[element_table.get_element("O")]

    def test_values(self):
        e1 = element_table.get_element("Pb")
        e2 = element_table.get_element("Pu")
        self.assertEqual(type(e1.b), complex)
        self.assertEqual(type(e1.Z), int)
        self.assertEqual(type(e2.b), complex)
        self.assertEqual(type(e2.Z), int)

    def test_properties(self):
        e1 = element_table.get_element("Pb")
        e2 = element_table.get_element("Pu")
        self.assertEqual(type(e1.E), np.ndarray)
        self.assertEqual(type(e1.f), np.ndarray)
        self.assertEqual(type(e1.fp), np.ndarray)
        self.assertEqual(type(e1.fpp), np.ndarray)
        self.assertEqual(type(e1.f_of_E(8.0)), np.complex128)
        self.assertTrue(np.isnan(e2.f_of_E(8.0)))
