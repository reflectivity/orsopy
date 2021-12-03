import json
import unittest

from datetime import datetime

from numpy import array, ndarray, testing

from orsopy.slddb.converters import (CArray, CComplex, CDate, Cdoi, CFormula, CLimited, CMultiSelect, Converter,
                                     CSelect, CType, CUrl)
from orsopy.slddb.material import Formula


class TestConverter(unittest.TestCase):
    def test_int(self):
        conv = CType(int, int)
        self.assertEqual(14, conv.revert(conv.convert(14)))
        self.assertEqual(conv.sql_type, "INT")

        self.assertTrue(type(conv.convert("13")) is int)
        self.assertTrue(type(conv.revert(13)) is int)

        with self.assertRaises(ValueError):
            conv.convert("13.4")
        with self.assertRaises(ValueError):
            conv.revert("13")

    def test_float(self):
        conv = CType(float, float)
        self.assertEqual(14.5, conv.revert(conv.convert(14.5)))
        self.assertEqual(conv.sql_type, "REAL")

        self.assertTrue(type(conv.convert("13.5")) is float)
        self.assertTrue(type(conv.revert(13.5)) is float)

        with self.assertRaises(ValueError):
            conv.convert("13a")
        with self.assertRaises(ValueError):
            conv.revert("13.5")

    def test_complex(self):
        conv = CComplex()
        self.assertEqual(14.5 + 3j, conv.revert(conv.convert(14.5 + 3j)))

        with self.assertRaises(ValueError):
            conv.convert("13a")
        with self.assertRaises(TypeError):
            conv.convert(b"abc")
        with self.assertRaises(ValueError):
            conv.revert(b"13.5")
        with self.assertRaises(TypeError):
            conv.revert("13.5")

    def test_str(self):
        conv = CType(str, str)
        self.assertEqual("abc", conv.revert(conv.convert("abc")))
        self.assertEqual(conv.sql_type, "TEXT")

        self.assertTrue(type(conv.convert("13")) is str)
        self.assertTrue(type(conv.revert("13")) is str)

        with self.assertRaises(ValueError):
            conv.revert(b"abc")
        with self.assertRaises(ValueError):
            conv.revert(14)

    def test_bytes(self):
        conv = CType(bytes, bytes)
        self.assertEqual(b"abc", conv.revert(conv.convert(b"abc")))
        self.assertEqual(conv.sql_type, "BLOB")

        self.assertTrue(type(conv.convert(b"13")) is bytes)
        self.assertTrue(type(conv.revert(b"13")) is bytes)

        with self.assertRaises(ValueError):
            conv.revert("abc")
        with self.assertRaises(ValueError):
            conv.revert(14)

    def test_formula(self):
        conv = CFormula()
        start_formula = Formula("Fe2O3")
        self.assertEqual(str(start_formula), conv.revert(conv.convert(str(start_formula))))
        self.assertEqual(str(start_formula), conv.revert(conv.convert(start_formula)))
        with self.assertRaises(ValueError):
            conv.convert("z1o")

    def test_url(self):
        conv = CUrl()
        self.assertEqual("http://www.abc.de", conv.revert(conv.convert("http://www.abc.de")))
        self.assertEqual("https://www.abc.de", conv.revert(conv.convert("https://www.abc.de")))
        self.assertEqual(conv.sql_type, "TEXT")

        self.assertTrue(type(conv.convert("http://www.abc.de")) is str)
        self.assertTrue(type(conv.revert("http://www.abc.de")) is str)

        with self.assertRaises(ValueError):
            conv.convert("abc")
        with self.assertRaises(ValueError):
            conv.revert(14)
        with self.assertRaises(ValueError):
            conv.convert("https://abc")
        with self.assertRaises(ValueError):
            conv.convert("ftp://www.abc.de")
        with self.assertRaises(ValueError):
            conv.convert("ssh://www.abc.de")
        with self.assertRaises(ValueError):
            conv.revert(b"abc")

    def test_doi(self):
        conv = Cdoi()
        self.assertEqual(
            "https://doi.org/10.1107/S2052520616017935", conv.revert(conv.convert("10.1107/S2052520616017935"))
        )
        self.assertEqual(
            "https://doi.org/10.1107/S2052520616017935",
            conv.revert(conv.convert("https://doi.org/10.1107/S2052520616017935")),
        )
        self.assertEqual(conv.sql_type, "TEXT")

        self.assertTrue(type(conv.convert("https://doi.org/10.1107/S2052520616017935")) is str)

        with self.assertRaises(ValueError):
            conv.convert("http://doi.org/10.1107/S2052520616017935")
        with self.assertRaises(ValueError):
            conv.convert("ftp://www.abc.de")
        with self.assertRaises(ValueError):
            conv.convert("https://www.abc.de")

    def test_date(self):
        conv = CDate()
        now = datetime.now()
        # round off the sub-seconds
        now = datetime.strptime(now.strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S")
        self.assertEqual(now, conv.revert(conv.convert(now)))
        self.assertEqual(now, conv.revert(conv.convert(now.strftime("%Y-%m-%d %H:%M:%S"))))

    def test_select(self):
        conv = CSelect(["o1", "o2", "o3"])

        self.assertEqual("o1", conv.revert(conv.convert("o1")))
        with self.assertRaises(ValueError):
            conv.convert("o4")

    def test_multiselect(self):
        conv = CMultiSelect(["o1", "o2", "o3"])

        self.assertEqual(["o1"], conv.revert(conv.convert(["o1"])))
        self.assertEqual(["o2", "o1"], conv.revert(conv.convert(["o2", "o1"])))
        with self.assertRaises(ValueError):
            conv.convert(["o4"])

    def test_non_sqtype(self):
        with self.assertRaises(TypeError):
            CType(str, array)

    def test_limited_float(self):
        conv = CLimited(float, float, -3.0, 5.4)
        self.assertEqual(3.5, conv.revert(conv.convert(3.5)))
        self.assertEqual(conv.sql_type, "REAL")

        self.assertTrue(type(conv.convert("3.5")) is float)
        self.assertTrue(type(conv.revert(3.5)) is float)

        with self.assertRaises(ValueError):
            conv.convert("13a")
        with self.assertRaises(ValueError):
            conv.revert("13.5")
        self.assertTrue(conv.validate(-3.0))
        self.assertTrue(conv.validate(5.4))
        self.assertFalse(conv.validate(-3.1))
        self.assertFalse(conv.validate(5.5))

    def test_array_general(self):
        conv = CArray()
        a = array([1, 2, 4, 5, 6])
        b = array([[1, 2], [3, 4]])

        self.assertTrue(type(conv.revert(conv.convert(a))) is ndarray)

        testing.assert_array_equal(a, conv.revert(conv.convert(a)))
        testing.assert_array_equal(b, conv.revert(conv.convert(b)))

        self.assertIsNone(conv.revert(None))
        with self.assertRaises(TypeError):
            conv.revert(conv.convert(a).decode("ascii"))

    def test_array_dimension(self):
        conv = CArray(ndim=1)
        a = array([1, 2, 4, 5, 6])
        testing.assert_array_equal(a, conv.revert(conv.convert(a)))

        with self.assertRaises(ValueError):
            b = array([[1, 2], [3, 4]])
            conv.revert(conv.convert(b))

    def test_array_shape(self):
        conv = CArray(shape=(2, 2))

        with self.assertRaises(ValueError):
            a = array([1, 2, 4, 5, 6])
            conv.convert(a)
        with self.assertRaises(ValueError):
            a = array([[1, 2, 4], [5, 6, 7]])
            conv.convert(a)

        b = array([[1, 2], [3, 4]])
        testing.assert_array_equal(b, conv.revert(conv.convert(b)))

    def test_class(self):
        class Test(Converter):
            def __init__(self):
                pass

        with self.assertRaises(TypeError):
            Test()

    def test_validate(self):
        conv = CType(float, float)
        self.assertTrue(conv.validate(13.4))
        self.assertFalse(conv.validate("abc"))

        conv = CLimited(float, float, -3.0, 5.4)
        self.assertFalse(conv.validate(-4.0))
        self.assertFalse(conv.validate("abc"))

    def test_serialize(self):
        conv = CType(float, float)
        json.dumps(conv.revert_serializable(2.3))

        conv = CDate()
        now = datetime.now()
        # round off the sub-seconds
        now = now.strftime("%Y-%m-%d %H:%M:%S")
        json.dumps(conv.revert_serializable(now))

        conv = CComplex()
        json.dumps(conv.revert_serializable(None))
        json.dumps(conv.revert_serializable(conv.convert(14.5 + 3j)))

        conv = CArray()
        a = array([1, 2, 4, 5, 6])
        c = array([1, 2, 4, 5, 6], dtype=complex)
        json.dumps(conv.revert_serializable(None))
        json.dumps(conv.revert_serializable(conv.convert(a)))
        json.dumps(conv.revert_serializable(conv.convert(c)))

    def test_html(self):
        for conv in [
            CType(float, float),
            CFormula(),
            CLimited(float, float, 0.0, 3.4),
            CComplex(),
            CSelect(["abc", "def", "ghi"]),
            CMultiSelect(["abc", "def", "ghi"]),
            CDate(),
            CUrl(),
        ]:
            conv.html_input("abc", "def")
