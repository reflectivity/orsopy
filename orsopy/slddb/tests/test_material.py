import unittest

from numpy.testing import assert_array_equal

from orsopy.slddb.constants import Cu_kalpha, Cu_kalpha1, Mo_kalpha, Mo_kalpha1
from orsopy.slddb.element_table import Element, element
from orsopy.slddb.element_table.nlengths import NEUTRON_SCATTERING_LENGTHS
# reference data uses Henke tables
from orsopy.slddb.element_table.xray_henke import XRAY_SCATTERING_FACTORS
from orsopy.slddb.material import Formula, Material

element.XRAY_SCATTERING_FACTORS = XRAY_SCATTERING_FACTORS
# import other n_lengths for coverage

# calculated using NIST calculator at https://www.ncnr.nist.gov/resources/activation/
REFERENCE_RESULTS = {
    # compound: [neutron, xray Cu, xray Mo]
    "Ni": [9.406e-6 - 0.001e-6j, 64.390e-6 - 1.351e-6j, 72.969e-6 - 2.894e-6j],  # dens=8.9
    "Fe2O3": [7.176e-6 - 0j, 41.125e-6 - 3.635e-6j, 42.740e-6 - 0.956e-6j],  # dens=5.24
    "D2O": [6.393e-6 - 0j, 9.455e-6 - 0.032e-6j, 9.416e-6 - 0.006e-6j],  # dens=1.11
}


class TestMaterial(unittest.TestCase):
    def test_density(self):
        m1 = Material([(Element("Ni"), 1.0)], dens=8.9)
        m2 = Material([(Element("Fe"), 2.0), (Element("O"), 3.0)], dens=5.24)
        self.assertAlmostEqual(m1.dens, 8.9)
        self.assertAlmostEqual(m2.dens, 5.24)
        with self.assertRaises(ValueError):
            Material([(Element("Ni"), 1.0)], dens=5.0, fu_dens=1.04)

    def test_volume(self):
        m1 = Material([(Element("Ni"), 1.0)], fu_volume=10.950863331638253)
        m2 = Material([(Element("Fe"), 2.0), (Element("O"), 3.0)], fu_volume=50.60467453722025)
        m3 = Material([(Element("Ni"), 1.0)], fu_dens=1.0 / 10.950863331638253)
        self.assertAlmostEqual(m1.dens, 8.9, places=6)
        self.assertAlmostEqual(m2.dens, 5.24, places=6)
        self.assertAlmostEqual(m1.dens, m3.dens, places=6)
        self.assertAlmostEqual(m1.fu_volume, 10.950863331638253, places=10)
        self.assertAlmostEqual(m2.fu_volume, 50.60467453722025, places=10)
        self.assertAlmostEqual(m3.fu_volume, 10.950863331638253, places=10)
        with self.assertRaises(ValueError):
            Material([(Element("Ni"), 1.0)], dens=5.0, fu_volume=10.950864)

    def test_rho_n(self):
        m1 = Material([(Element("Ni"), 1.0)], rho_n=REFERENCE_RESULTS["Ni"][0])
        m2 = Material([(Element("Fe"), 2.0), (Element("O"), 3.0)], rho_n=REFERENCE_RESULTS["Fe2O3"][0])
        self.assertAlmostEqual(m1.dens, 8.9, places=3)
        self.assertAlmostEqual(m2.dens, 5.24, places=3)

    def test_rho_x(self):
        m1 = Material([(Element("Ni"), 1.0)], xsld=REFERENCE_RESULTS["Ni"][2], xE=Mo_kalpha)
        m2 = Material([(Element("Fe"), 2.0), (Element("O"), 3.0)], xsld=REFERENCE_RESULTS["Fe2O3"][1], xE=Cu_kalpha)
        self.assertAlmostEqual(m1.dens, 8.9, places=3)
        self.assertAlmostEqual(m2.dens, 5.24, places=3)

    def test_formula(self):
        m1 = Material([(Element("Ni"), 1.0)], xsld=REFERENCE_RESULTS["Ni"][2], xE=Mo_kalpha)
        self.assertEqual(str(m1.formula), "Ni")
        self.assertEqual(m1.formula, Formula([("Ni", 1.0)]))

    def test_creation(self):
        Material([(Element("Ni"), 1.0)], dens=1.0)
        Material("Ni", dens=1.0)
        Material(Formula("Ni"), dens=1.0)
        with self.assertRaises(TypeError):
            Material(123.4, dens=1.0)

    def test_combine(self):
        m1 = Material([(Element("Ni"), 1.0)], fu_volume=1.0)
        m2 = Material([(Element("Co"), 1.0)], fu_volume=1.0)
        ms = m1 + m2
        mss = m1 + m1
        mp1 = 2.0 * m1
        mp2 = m2 * 2.0
        self.assertEqual(str(ms.formula), "CoNi")
        self.assertEqual(str(mss.formula), "Ni2")
        self.assertEqual(ms.fu_volume, 2.0)
        self.assertEqual(mp1.fu_volume, 2.0)
        self.assertEqual(mp2.fu_volume, 2.0)
        fs = m1.formula + m2.formula + m2.formula
        self.assertEqual(str(fs), "Co2Ni")

        with self.assertRaises(ValueError):
            m1 + "abc"
        with self.assertRaises(ValueError):
            "abc" * m1

    def test_formula_calculations(self):
        f1 = Formula("O")
        f2 = Formula("H")
        self.assertEqual(2 * f2 + f1, Formula("H2O"))
        self.assertEqual(2 * f2 - f2, f2)

    def test_fail(self):
        with self.assertRaises(ValueError):
            Material([(Element("Ni"), 1.0)])
        with self.assertRaises(ValueError):
            Material([(Element("Pu"), 1.0)], dens=20.0)
        with self.assertRaises(ValueError):
            Material([(Element("Po"), 1.0)], dens=20.0)
        mok = Material("Ni", dens=1.0)
        with self.assertRaises(ValueError):
            -1 * mok

    def test_neutron_ni(self):
        m1 = Material([(Element("Ni"), 1.0)], dens=8.9)

        # compare with value from NIST
        self.assertAlmostEqual(m1.rho_n.real, REFERENCE_RESULTS["Ni"][0].real)
        self.assertAlmostEqual(m1.rho_n.imag, REFERENCE_RESULTS["Ni"][0].imag)

    def test_neutron_d2o(self):
        m1 = Material([(Element("D"), 2.0), (Element("O"), 1.0)], dens=1.11)
        m2 = Material([(Element("H[2]"), 2.0), (Element("O"), 1.0)], dens=1.11)

        # compare with value from NIST
        self.assertAlmostEqual(m1.rho_n.real, REFERENCE_RESULTS["D2O"][0].real)
        self.assertAlmostEqual(m1.rho_n.imag, REFERENCE_RESULTS["D2O"][0].imag)
        self.assertEqual(m1.rho_n, m2.rho_n)

    def test_neutron_fe2o3(self):
        m2 = Material([(Element("Fe"), 2.0), (Element("O"), 3.0)], dens=5.24)

        # compare with value from NIST
        self.assertAlmostEqual(m2.rho_n.real, REFERENCE_RESULTS["Fe2O3"][0].real)
        self.assertAlmostEqual(m2.rho_n.imag, REFERENCE_RESULTS["Fe2O3"][0].imag)

    def test_xray_kalpha(self):
        m2 = Material([(Element("Fe"), 2.0), (Element("O"), 3.0)], dens=5.24)

        # compare calculated values with known parameters from external sources
        with self.subTest("Cu", i=0):
            sld = m2.rho_of_E(Cu_kalpha)
            # sld-calculator.appspot.com: 4.1125e-05  	-3.6347e-06
            self.assertAlmostEqual(sld.real, 4.1125e-05)
            self.assertAlmostEqual(sld.imag, -3.6347e-06)
            # Henke: 8047.82959 eV  delta=1.55382077E-05  beta=1.37184929E-06
            self.assertAlmostEqual(m2.delta_of_E(Cu_kalpha1), 1.55382e-05, places=5)
            self.assertAlmostEqual(m2.beta_of_E(Cu_kalpha1), 1.37185e-06, places=5)
            # Henke: 8047.83 eV  mu=8.93664 µm
            self.assertAlmostEqual(m2.mu_of_E(Cu_kalpha1), 1.0 / 8.93664e4, places=5)
        with self.subTest("Mo", i=1):
            sld = m2.rho_of_E(Mo_kalpha)
            # sld-calculator.appspot.com: 4.274e-05  	-9.5604e-07
            self.assertAlmostEqual(sld.real, 4.274e-05)
            self.assertAlmostEqual(sld.imag, -9.5604e-07)
            # Henke: 17479.4004 eV  delta=3.4223483E-06  beta=7.66335759E-08
            self.assertAlmostEqual(m2.delta_of_E(Mo_kalpha1), 3.4223483e-06, places=5)
            self.assertAlmostEqual(m2.beta_of_E(Mo_kalpha1), 7.66335759e-08, places=5)
            # Henke: 17479.4 eV  mu=73.6570 µm
            self.assertAlmostEqual(m2.mu_of_E(Mo_kalpha1), 1.0 / 73.6570e4, places=5)

    def test_xray_all(self):
        m2 = Material([(Element("Fe"), 2.0), (Element("O"), 3.0)], dens=5.24)
        E1, rho = m2.rho_vs_E()
        E2, delta = m2.delta_vs_E()
        E3, beta = m2.beta_vs_E()
        E4, mu = m2.mu_vs_E()
        assert_array_equal(E1, E2)
        assert_array_equal(E1, E3)
        assert_array_equal(E1, E4)

    def test_magnetic(self):
        m0 = Material([(Element("Fe"), 2.0), (Element("O"), 3.0)], dens=5.24)
        m1 = Material([(Element("Fe"), 2.0), (Element("O"), 3.0)], dens=5.24, mu=3.5)
        m2 = Material([(Element("Fe"), 2.0), (Element("O"), 3.0)], dens=5.24, M=m1.M)
        self.assertEqual(m0.rho_m, 0.0)
        self.assertEqual(m0.M, 0.0)
        self.assertAlmostEqual(m1.mu, m2.mu)
        self.assertAlmostEqual(m1.rho_m, m2.rho_m)
        self.assertAlmostEqual(m1.M, m2.M)
        with self.assertRaises(ValueError):
            Material([(Element("Fe"), 2.0), (Element("O"), 3.0)], dens=5.24, mu=m1.mu, M=m1.M)

    def test_string_conversion(self):
        m2 = Material([(Element("Mo"), 1.0), (Element("Fe"), 2.0), (Element("O"), 3.2)], dens=5.24, ID=13)
        str(m2)
        repr(m2)
        m2 = Material(
            [(Element("Mo"), 1.0), (Element("Fe"), 2.0), (Element("O"), 3.2)], dens=5.24, ID=None, name="MoFeO"
        )
        str(m2)
        repr(m2)

    def test_dict_conversion(self):
        m1 = Material([(Element("Mo"), 1.0), (Element("Fe"), 2.0), (Element("O"), 3.2)], dens=5.24, ID=13)
        m1.export(xray_units="sld")
        m1.export(xray_units="n_db")
        m1.export(xray_units="edens")
        with self.assertRaises(ValueError):
            m1.export(xray_units="test")
        m2 = Material("B[10]4C", dens=2.55)
        m2.export()

    def test_missing_data(self):
        with self.assertRaises(ValueError):
            Element()
        e = Element("Mo")
        self.assertEqual(e.f_of_E(1e10), 0.0 + 0j)

    def test_element_properties(self):
        e = Element("Mo")
        self.assertEqual(e.E.shape, e.f.shape)
        self.assertEqual(e.E.shape, e.fp.shape)
        self.assertEqual(e.E.shape, e.fpp.shape)
        self.assertEqual(e.Lamda.shape, e.b_lambda.shape)
        n = Element("Gd")
        self.assertEqual(n.Lamda.shape, n.b_abs.shape)
        self.assertEqual(n.Lamda.shape, n.b_lambda.shape)

    def test_lambda_interpolation(self):
        n = Element("B")
        self.assertAlmostEqual(n.b.imag, n.b_of_L(1.798).imag, 2)
        n.b_of_L(0)
        n.b_of_L(1000)
        m = Material("B", dens=2.5)
        self.assertAlmostEqual(m.rho_n.imag, m.rho_n_of_L(1.798).imag, 2)
        Material("O", dens=2.5).b_vs_L()

    def test_element_strings(self):
        e = Element("H")
        str(e)
        repr(e)
        e = Element("H[2]")
        str(e)
        repr(e)

    def test_deuteration(self):
        m1 = Material("H2O", dens=1.0)
        m2 = Material("D2O", fu_dens=m1.fu_dens)
        m3 = Material("HHxO", fu_dens=m1.fu_dens, name="exchangable")
        m4 = Material("HDO", fu_dens=m1.fu_dens)
        self.assertEqual(m1.deuterated.formula, m2.formula)
        self.assertAlmostEqual(m1.deuterated.fu_dens, m2.fu_dens)
        self.assertEqual(m3.deuterated.formula, m2.formula)
        self.assertAlmostEqual(m3.deuterated.fu_dens, m2.fu_dens)
        self.assertEqual(m1.deuterate(0.5).formula, m4.formula)
        self.assertAlmostEqual(m1.deuterate(0.5).fu_dens, m4.fu_dens)
        self.assertEqual(m3.edeuterated.formula, Formula("DHxO"))
        Material("HHxO", fu_dens=m1.fu_dens).edeuterated  # check the case of name=None

    def test_exchange(self):
        m1 = Material("H2O", dens=1.0)
        m3 = Material("HHxO", fu_dens=m1.fu_dens)
        m3a = Material("HHxO", fu_dens=m1.fu_dens, name="test")
        m4 = Material("HDO", dens=1.0)
        self.assertEqual(m1.formula, m3.not_exchanged.formula)
        self.assertEqual(m4.formula, m3.exchanged.formula)
        self.assertAlmostEqual(m3a.not_exchanged.fu_dens, m1.fu_dens)
        self.assertAlmostEqual(m3a.exchanged.fu_dens, m1.fu_dens)

    def test_match_point(self):
        m1 = Material("H2O", dens=1.0)
        m2 = Material("D2O", fu_dens=m1.fu_dens)
        # replace D2O with one that has equal volume
        from orsopy.slddb import material

        material.H2O = m1
        material.D2O = m2
        self.assertAlmostEqual((m1 + m2).match_point, 0.5)
        self.assertAlmostEqual((3 * m1 + m2).match_point, 0.25)
        self.assertAlmostEqual((m1 + 3 * m2).match_point, 0.75)

        m3 = Material("HDHx2O2", fu_dens=m1.fu_dens / 2.0)
        self.assertAlmostEqual(m3.match_point, 0.5 / 1.1)
        m4 = Material("D3O", fu_dens=m1.fu_dens)
        self.assertTrue(m4.match_point > 1.0)
