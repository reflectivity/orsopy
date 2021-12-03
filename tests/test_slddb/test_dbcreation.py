import sys
import unittest

from numpy import ndarray, testing

from orsopy.slddb import SLDDB, dbconfig, element_table


class TestCreateDB(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = SLDDB(":memory:")
        cls.db.create_database()

    @classmethod
    def tearDownClass(cls):
        del cls.db

    def test_tables(self):
        c = self.db.db.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        items = c.fetchall()
        for i, tbl in enumerate([dbconfig.DB_MATERIALS_NAME]):
            with self.subTest(msg=tbl, i=i):
                self.assertTrue((tbl,) in items)

    def test_element_search(self):
        with self.subTest("database search", i=0):
            s1 = element_table.get_element("Si")
            s2 = element_table.get_element(14)
        with self.subTest("equality", i=0):
            self.assertEqual(s1.Z, s2.Z)
            self.assertEqual(s1.symbol, s2.symbol)
            self.assertEqual(s1.mass, s2.mass)
            self.assertEqual(s1.b, s2.b)
            testing.assert_array_equal(s1._xdata, s2._xdata)

    def test_add_field(self):
        global dbconfig
        # call without changes
        self.db.update_fields()

        # call with appending column
        dbconfig.DB_MATERIALS_FIELDS.append("testadd")
        dbconfig.DB_MATERIALS_CONVERTERS.append(dbconfig.DB_MATERIALS_CONVERTERS[-1])
        dbconfig.DB_MATERIALS_FIELD_DEFAULTS.append(dbconfig.DB_MATERIALS_FIELD_DEFAULTS[-1])
        dbconfig.db_lookup = dict(
            [
                (field, (i, converter, default))
                for i, (field, converter, default) in enumerate(
                    zip(
                        dbconfig.DB_MATERIALS_FIELDS,
                        dbconfig.DB_MATERIALS_CONVERTERS,
                        dbconfig.DB_MATERIALS_FIELD_DEFAULTS,
                    )
                )
            ]
        )

        self.db.update_fields()

        # call with inserted column
        dbconfig.DB_MATERIALS_FIELDS.insert(5, "testadd2")
        dbconfig.DB_MATERIALS_CONVERTERS.insert(5, dbconfig.DB_MATERIALS_CONVERTERS[-1])
        dbconfig.DB_MATERIALS_FIELD_DEFAULTS.insert(5, dbconfig.DB_MATERIALS_FIELD_DEFAULTS[-1])
        dbconfig.db_lookup = dict(
            [
                (field, (i, converter, default))
                for i, (field, converter, default) in enumerate(
                    zip(
                        dbconfig.DB_MATERIALS_FIELDS,
                        dbconfig.DB_MATERIALS_CONVERTERS,
                        dbconfig.DB_MATERIALS_FIELD_DEFAULTS,
                    )
                )
            ]
        )
        self.db.update_fields()

        # reset database
        dbconfig.DB_MATERIALS_FIELDS.pop(-1)
        dbconfig.DB_MATERIALS_FIELDS.pop(5)
        dbconfig.DB_MATERIALS_CONVERTERS.pop(-1)
        dbconfig.DB_MATERIALS_CONVERTERS.pop(5)
        dbconfig.DB_MATERIALS_FIELD_DEFAULTS.pop(-1)
        dbconfig.DB_MATERIALS_FIELD_DEFAULTS.pop(5)
        dbconfig.db_lookup = dict(
            [
                (field, (i, converter, default))
                for i, (field, converter, default) in enumerate(
                    zip(
                        dbconfig.DB_MATERIALS_FIELDS,
                        dbconfig.DB_MATERIALS_CONVERTERS,
                        dbconfig.DB_MATERIALS_FIELD_DEFAULTS,
                    )
                )
            ]
        )
        self.db = SLDDB(":memory:")
        self.db.create_database()

    def test_backup(self):
        if sys.version_info.minor > 6:
            self.db.backup(":memory:")
