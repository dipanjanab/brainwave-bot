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

    def test_fy26_nemia_count(self):
        result = ask("How many NEMIA stories were submitted in FY26?")
        self.assertEqual(result["answer"], "3 submitted stories in NEMIA during FY26.")


if __name__ == "__main__":
    unittest.main()
