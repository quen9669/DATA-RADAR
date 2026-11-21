import unittest
from salary import parse, to_eur

CASES = [  # text, annual_min, annual_max, currency, excluded
    ("CHF 85'000 - 95'000 par an", 85000, 95000, "CHF", None),
    ("60k-70k € par an", 60000, 70000, "EUR", None),
    ("3500 € brut/mois, 13e mois", 45500, 45500, "EUR", None),
    ("4 500 € par mois, temps partiel 80%", 67500, 67500, "EUR", None),
    ("50 €/h", 104000, 104000, "EUR", None),
    ("TJM 450 € par jour", None, None, "EUR", "freelance"),
    ("jusqu'à 70 000 € par an", None, None, "EUR", "cap_only"),
    ("5000 CHF net par mois", None, None, "CHF", "net"),
    ("Salaire : 4000 €", None, None, "EUR", "unknown_period"),
    ("20 000 - 90 000 € par an", 20000, 90000, "EUR", "range_too_wide"),
    ("500 € par an", 500, 500, "EUR", "out_of_bounds"),
]


class SalaryTest(unittest.TestCase):
    def test_cases(self):
        for text, lo, hi, cur, excluded in CASES:
            with self.subTest(text):
                r = parse(text)
                self.assertEqual((r["annual_min"], r["annual_max"], r["currency"], r["excluded"]), (lo, hi, cur, excluded))

    def test_no_salary(self):
        self.assertIsNone(parse("Salaire attractif selon profil"))
        self.assertIsNone(parse("Une équipe de 40 personnes, budget 5 M€"))

    def test_fx(self):
        self.assertEqual(to_eur(100000, "CHF"), 107000)
        self.assertEqual(to_eur(100000, "EUR"), 100000)


if __name__ == "__main__":
    unittest.main()
