import unittest

from orsopy.slddb.material import Formula


class TestFormula(unittest.TestCase):
    def test_valid(self):
        Formula("NaCl")
        Formula("H2 O")
        Formula("Cr3O4")
        Formula("H12 C5O8")
        Formula("H2O")

    def test_isotopes(self):
        Formula("B[10]4C")
        Formula("H[2]2O")
        Formula("OH[2]2")
        Formula("D2O")

    def test_compound_strings(self):
        self.assertEqual(Formula("Na(Cl)"), Formula("Na1Cl1"))
        self.assertEqual(Formula("(H)2 O"), Formula("H2O1"))
        self.assertEqual(Formula("Fe(HO3)2"), Formula("Fe1H2O6"))
        self.assertEqual(Formula("Fe1.5(HO3)2.5"), Formula("Fe1.5H2.5O7.5"))
        self.assertEqual(Formula("(NaCl)2"), Formula("Na2Cl2"))
        self.assertEqual(Formula("Cr(BO2)3(H2O)2"), Formula("Cr1B3O8H4"))
        self.assertEqual(Formula("(BO2)3Cr(H2O)2"), Formula("Cr1B3O8H4"))
        self.assertEqual(Formula("(BO2)3 Cr (H2O)2"), Formula("Cr1B3O8H4"))

    def test_invalid(self):
        with self.assertRaises(ValueError):
            Formula("z")
        with self.assertRaises(ValueError):
            Formula("")
        with self.assertRaises(ValueError):
            Formula("(Fe(BO)2)3")
        with self.assertRaises(ValueError):
            Formula("(FeBO23")

    def test_merge(self):
        f1 = Formula("NaCl")
        f2 = Formula("NaCl")
        self.assertEqual(f1, f2)

        f2 = Formula("Na1Cl1")
        self.assertEqual(f1, f2)
        f2 = Formula("Na0.5Na0.5Cl1")
        self.assertEqual(f1, f2)

        f2 = Formula("Na0.5Cl1Na0.5")
        self.assertEqual(f1, f2)

        f2 = Formula("ClNa1.0")
        self.assertEqual(f1, f2)

        f1 = Formula("H2O")
        f2 = Formula("OH2")
        self.assertEqual(f1, f2)

    def test_strparse(self):
        str(Formula("NaCl"))
        str(Formula("Na1Cl1.0"))
        str(Formula("Na0.5Cl2"))

    def test_contains(self):
        self.assertTrue("Cr" in Formula("Cr2O3"))
        self.assertEqual(0, Formula("Fe2O3").index("Fe"))
        self.assertEqual(1, Formula("Fe2O3").index("O"))

    def test_ambigous(self):
        self.assertEqual(Formula("CLa"), Formula("C1La1"))
        self.assertEqual(Formula("YB"), Formula("y1b1"))
        self.assertEqual(Formula("PTa"), Formula("P1Ta1"))
        self.assertEqual(Formula("BEu"), Formula("b1eu1"))
        self.assertEqual(Formula("SBEu"), Formula("s1b1eu1"))
        # lower case without numbers is not recommended, as it is not unique in many cases
        self.assertEqual(Formula("beu"), Formula("be1u1"))
        self.assertEqual(Formula("BEu"), Formula("b1eu1"))
