import json
import unittest

from orsopy.slddb import SLDDB
from orsopy.slddb.comparators import ExactString


class TestMaterialDB(unittest.TestCase):
    db: SLDDB

    @classmethod
    def setUpClass(cls):
        cls.db = SLDDB(":memory:")
        cls.db.create_database()

    def test_add_item(self):
        self.db.add_material("Iron Oxide 1", "Fe2O3", density=5.24)
        self.db.add_material("Nickel", "Ni", density="8.9")

        with self.assertRaises(KeyError):
            self.db.add_material("TestMaterial 1", "Fe2O3", beer="beer", density=2.0)
        with self.assertRaises(ValueError):
            self.db.add_material("TestMaterial 2", "Fe2O3")

    def test_update_item(self):
        self.db.add_material("Iron Oxide E1", "Fe2O3", density=5.24)
        res = self.db.search_material(name="Iron Oxide E1")[0]
        self.db.update_material(res["ID"], description="updated description")
        res2 = self.db.search_material(name="Iron Oxide E1")[0]
        self.assertEqual(res2["description"], "updated description")
        with self.assertRaises(KeyError):
            self.db.update_material(res["ID"], fail_key="updated description")
        with self.assertRaises(ValueError):
            self.db.update_material(res["ID"], density=None)

    def test_search(self):
        self.db.add_material("Iron Oxide 2", "Fe2O3", density=5.24, tags=["metal alloy"])
        self.db.add_material("Nickel 1", "Ni", density="8.9")

        res = self.db.search_material(name="oxide 2")[0]
        self.assertEqual(res["density"], 5.24)
        self.assertEqual(res["name"], "Iron Oxide 2")
        self.assertEqual(res["formula"], "Fe2O3")
        self.assertIsNone(res["FU_volume"])
        res = self.db.search_material(tags=["metal alloy"])[0]
        self.assertEqual(res["density"], 5.24)
        self.assertEqual(res["name"], "Iron Oxide 2")
        self.assertEqual(res["formula"], "Fe2O3")
        self.assertIsNone(res["FU_volume"])

    def test_comparators(self):
        self.db.add_material("Iron Oxide 3123", "Fe2O32", density=99.123, tags=["inorganic"])
        res = self.db.search_material(name=ExactString("oxide 3"))
        self.assertEqual(len(res), 0)
        res = self.db.search_material(name=ExactString("Iron Oxide 3123"))
        self.assertEqual(len(res), 1)
        # tests FormulaComparator
        res = self.db.search_material(formula="O32")
        self.assertEqual(len(res), 0)
        res = self.db.search_material(formula="~O32")
        self.assertEqual(len(res), 1)
        # tests FuzzyFloat
        res = self.db.search_material(density="99.123")
        self.assertEqual(len(res), 1)
        res = self.db.search_material(density="99.124")
        self.assertEqual(len(res), 0)
        res = self.db.search_material(density="~99.124")
        self.assertEqual(len(res), 1)
        res = self.db.search_material(density="99-100")
        self.assertEqual(len(res), 1)

    def test_count(self):
        self.db.add_material("Iron Oxide Count All", "Fe2O3", density=5.2411111, tags=["inorganic"])
        self.db.add_material("Nickel Count All", "Ni", density="8.9")

        res = self.db.count_material(name="count all")
        self.assertEqual(2, res)
        res = self.db.count_material(name="count all", tags=[])
        self.assertEqual(2, res)
        res = self.db.count_material(name="count all", density=8.9)
        self.assertEqual(1, res)
        res = self.db.count_material(name="count all", density=5.2411111, join_and=False)
        self.assertEqual(2, res)
        res = self.db.count_material(name="count all", tags=["inorganic"])
        self.assertEqual(1, res)
        res = self.db.count_material(name=ExactString("count all"), tags=["inorganic"])
        self.assertEqual(0, res)
        self.db.count_material()

    def test_serializable_search(self):
        self.db.add_material("Iron Oxide 3", "Fe2O3", density=5.24)
        res = self.db.search_material(name="iron", serializable=True)[0]
        json.dumps(res)

    def test_search_fail(self):
        with self.assertRaises(KeyError):
            self.db.search_material(beer="beer")
        self.db.add_material("Iron Oxide 4", "Fe2O3", density=5.24)
        with self.assertRaises(ValueError):
            self.db.add_material("Iron Oxide 4", "Fe2O3", density=5.24)

    def test_count_fail(self):
        with self.assertRaises(KeyError):
            self.db.count_material(beer="beer")

    def test_search_empty(self):
        res = self.db.search_material()
        res2 = self.db.search_material()
        self.assertEqual(res[0]["accessed"], res2[0]["accessed"])

    def test_search_andor(self):
        self.db.add_material("Iron Oxide light", "Fe2O3", density=5.0)
        self.db.add_material("Iron Oxide heavy", "Fe2O3", density=6.0)
        res1 = self.db.search_material(name="iron", density=5.0)
        res2 = self.db.search_material(name="iron", density=5.0, join_and=False)
        self.assertNotEqual(res1, res2)

    def test_selection(self):
        self.db.add_material("To Select", "Pb", density=11.4)
        self.db.add_material("Nickel false", "Ni", FU_volume=10.5)
        res = self.db.search_material(density=11.4)
        mat = self.db.select_material(res[0])
        self.assertAlmostEqual(mat.dens, 11.4)
        res = self.db.search_material(FU_volume=10.5)
        mat = self.db.select_material(res[0])
        self.assertEqual(mat.fu_volume, 10.5)
        self.db.invalidate_material(res[0]["ID"], "testuser")
        res = self.db.search_material(FU_volume=10.5, filter_invalid=False)
        mat = self.db.select_material(res[0])
        self.assertEqual(mat.fu_volume, 10.5)

    def test_validate_item(self):
        self.db.add_material("To Validate", "Pb", density=11.4)
        res = self.db.search_material(name="To Validate", density=11.4)
        self.db.validate_material(res[0]["ID"], "testuser")
        res2 = self.db.search_material(ID=res[0]["ID"])
        self.assertIsNotNone(res2[0]["validated"])

    def test_invalidate_item(self):
        self.db.add_material("To Invalidate", "Pb", density=11.4)
        res = self.db.search_material(name="To Invalidate", density=11.4)
        self.db.invalidate_material(res[0]["ID"], "testuser")
        res2 = self.db.search_material(ID=res[0]["ID"], filter_invalid=False)
        self.assertIsNotNone(res2[0]["invalid"])
        res = self.db.search_material(name="To Invalidate", density=11.4)
        self.assertEqual(0, len(res))

    def test_tags(self):
        self.db.add_material("Tag it", "Pb", density=11.4, tags=["magnetic", "metal"])
        res = self.db.search_material(name="Tag it")
        del res[0]["accessed"]
        res2 = self.db.search_material(tags=["magnetic"])
        del res2[0]["accessed"]
        self.assertEqual(res, res2)
        res2 = self.db.search_material(tags=["metal"])
        del res2[0]["accessed"]
        self.assertEqual(res, res2)
        res2 = self.db.search_material(tags=["magnetic", "metal"])
        del res2[0]["accessed"]
        self.assertEqual(res, res2)
        res2 = self.db.search_material(tags=["polymer"])
        self.assertEqual(len(res2), 0)
        res2 = self.db.search_material(name="Tag it", tags=[])
        self.assertNotEqual(len(res2), 0)
        del res2[0]["accessed"]
        self.assertEqual(res, res2)

    def test_access_counter(self):
        self.db.add_material("Iron Oxide 5", "Fe2O3", density=5.24)
        r1 = self.db.search_material(name="iron")[0]["accessed"]
        r2 = self.db.search_material(name="iron")[0]["accessed"]
        r3 = self.db.search_material(name="iron")[0]["accessed"]
        self.assertEqual(r1 + 1, r2)
        self.assertEqual(r2 + 1, r3)
