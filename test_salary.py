import csv
import unittest
from salary import SEEDS, parse, to_eur

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
    ("Salary: EUR 6 000 gross monthly, paid over 13 months", 78000, 78000, "EUR", None),
    ("Verdienen Sie CHF 24.70 und CHF 28.00 pro Stunde", 51376, 58240, "CHF", None),
    ("Gehalt: CHF57’000\\.00 \\- CHF63’000\\.00 pro Jahr", 57000, 63000, "CHF", None),
    ("Payment : 19.2231 - 25.0 EUR / heure", 39984, 52000, "EUR", None),
    ("Rémunération : 2295 CHF brut par mois, 25 heures par semaine", 44064, 44064, "CHF", None),
    ("Provision auf jeden Abschluss: 3'000 bis 6'000 € im Monat", None, None, "EUR", "variable"),
    ("Salaire entre 55.000 et 85.000 EUR brut", 55000, 85000, "EUR", None),
    ("Gehalt: ab CHF4’200.00 pro Monat", None, None, "CHF", "floor_only"),
]


class SalaryTest(unittest.TestCase):
    def test_cases(self):
        for text, lo, hi, cur, excluded in CASES:
            with self.subTest(text):
                r = parse(text)
                self.assertEqual((r["annual_min"], r["annual_max"], r["currency"], r["excluded"]), (lo, hi, cur, excluded))

    def test_malformed_number(self):
        self.assertIsNone(parse("Salaire 2.910.00 € par mois"))

    def test_no_salary(self):
        self.assertIsNone(parse("Salaire attractif selon profil"))
        self.assertIsNone(parse("Une équipe de 40 personnes, budget 5 M€"))

    def test_precision_on_annotated_extracts(self):
        kept = good = 0
        with open(SEEDS / "salary_labels.csv", newline="") as f:
            rows = list(csv.DictReader(f))
        for r in rows:
            p = parse(r["context"])
            if r["label"] == "ambiguous" or not p or p["excluded"]:
                continue
            kept += 1
            good += r["label"] == "salary" and all(abs(p[f"annual_{k}"] - float(r[f"annual_{k}"])) <= 0.01 * float(r[f"annual_{k}"]) for k in ("min", "max"))
        self.assertGreaterEqual(good / kept, 0.95, f"{good}/{kept}")

    def test_fx(self):
        self.assertEqual(to_eur(100000, "CHF"), 107000)
        self.assertEqual(to_eur(100000, "EUR"), 100000)


if __name__ == "__main__":
    unittest.main()
