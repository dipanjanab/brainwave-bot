import unittest
from app.database.seed import seed_database
from app.services.sql_validator import validate_sql
from app.main import ask


class SqlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        seed_database()

    def test_blocks_mutation(self):
        with self.assertRaises(ValueError):
            validate_sql("DELETE FROM stories")

    def test_fy26_emia_count(self):
        result = ask("How many EMIA stories were submitted in FY26?")
        self.assertEqual(result["answer"], "3 submitted stories in EMIA during FY26.")

    def test_explicit_apac_filter(self):
        result = ask("How many stories were submitted?", market="APAC")
        self.assertEqual(result["answer"], "2 submitted stories in APAC.")
        self.assertEqual(result["parameters"], ["APAC"])

    def test_explicit_amer_filter(self):
        result = ask("How many stories were submitted?", market="AMER")
        self.assertEqual(result["answer"], "1 submitted stories in AMER.")
        self.assertEqual(result["parameters"], ["AMER"])

    def test_explicit_latam_filter(self):
        result = ask("How many stories were submitted?", market="LATAM")
        self.assertEqual(result["answer"], "1 submitted stories in LATAM.")
        self.assertEqual(result["parameters"], ["LATAM"])

    def test_rejects_unknown_explicit_market(self):
        with self.assertRaises(ValueError):
            ask("How many stories were submitted?", market="UNKNOWN")


if __name__ == "__main__":
    unittest.main()
