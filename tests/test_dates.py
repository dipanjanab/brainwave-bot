from datetime import date
import unittest
from app.services.date_resolver import get_current_fiscal_year, resolve_fiscal_year, resolve_period


class DateResolverTests(unittest.TestCase):
    def test_fy26_bounds(self):
        result = resolve_fiscal_year("FY26")
        self.assertEqual(result["start_date"], date(2025, 4, 1))
        self.assertEqual(result["end_date"], date(2026, 4, 1))

    def test_current_fiscal_year(self):
        self.assertEqual(get_current_fiscal_year(date(2026, 9, 2)), "FY27")

    def test_ytd(self):
        result = resolve_period("NEMIA YTD", today=date(2026, 9, 2))
        self.assertEqual(result["label"], "FY27 YTD")
        self.assertEqual(result["start_date"], date(2026, 4, 1))


if __name__ == "__main__":
    unittest.main()
