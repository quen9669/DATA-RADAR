"""Salary text -> annual gross full-time amount. Pure stdlib; seeds hold the rules."""
import csv, pathlib, re

SEEDS = pathlib.Path(__file__).parent / "dbt" / "seeds"
CUR = r"(chf|sfr|fr\.|€|eur(?:os?)?\b|\$|usd|£|gbp)"
NUM = r"(\d{1,3}(?:[ '’.,\u202f\u00a0]\d{3})+(?:[.,]\d{1,2})?|\d+(?:[.,]\d{1,2})?)\s*(k\b)?"
KEY = re.compile(r"salaire|salary|r[ée]mun[ée]ration|gehalt|lohn|verg[üu]tung|brut|gross|package|compensation|pay\\b")
SEP = r"(?:-|–|—|à|to|bis|et)"
AMOUNT = re.compile(rf"(?:{CUR}\s*)?{NUM}\s*{CUR}?(?:\s*{SEP}\s*(?:{CUR}\s*)?{NUM}\s*{CUR}?)?", re.I)
PERIODS = [("hour", r"/\s*h\b|heure|hour|hourly|stunde"), ("day", r"/\s*j\b|jour|\bday\b|daily|tag\b|tagessatz"),
           ("month", r"mois|month|monat|mensuel"), ("year", r"\ban\b|année|year|annuel|annual|jahr|p\.a\.|/\s*a\b")]
CODES = {"€": "EUR", "eur": "EUR", "euro": "EUR", "euros": "EUR", "$": "USD", "usd": "USD", "£": "GBP", "gbp": "GBP"}


def seed(name):
    with open(SEEDS / f"{name}.csv", newline="") as f:
        return {r["currency"]: r for r in csv.DictReader(f)}


def num(s, k):
    s = re.sub(r"[ '’\u202f\u00a0]", "", s)
    s = re.sub(r"[.,]", "", s) if re.fullmatch(r"\d{1,3}([.,]\d{3})+", s) else s.replace(",", ".")
    return float(s) * (1000 if k else 1)


def parse(text, hours=40.0):
    """First amount that looks like a salary -> dict(min, max, currency, period, context, annual_min, annual_max, excluded), else None."""
    t = text.lower()
    for m in AMOUNT.finditer(t):
        c1, a, k1, c2, c3, b, k2, c4 = m.groups()
        cur = next((c for c in (c1, c2, c3, c4) if c), None)
        w = t[max(0, m.start() - 80):m.end() + 60]
        after = t[m.end():m.end() + 30]
        if cur and (KEY.search(t[max(0, m.start() - 60):m.start()]) or any(re.search(rx, after) for _, rx in PERIODS)):
            try:
                lo, hi = num(a, k1), num(b, k2 or k1) if b else None
            except ValueError:  # e.g. "2.910.00": not an amount
                continue
            break
    else:
        return None
    cur = CODES.get(cur, "CHF" if cur in ("chf", "sfr", "fr.") else cur.upper())
    period = next((p for p, rx in PERIODS if re.search(rx, after)), None) or next((p for p, rx in PERIODS if re.search(rx, w)), None)
    out = dict(min=lo, max=hi or lo, currency=cur, period=period, context=text[max(0, m.start() - 120):m.end() + 80], annual_min=None, annual_max=None, excluded=None)
    if re.search(r"\bnet\b|netto", w):
        out["excluded"] = "net"
    elif re.search(r"tjm|freelance|taux journalier|tagessatz|daily rate", w):
        out["excluded"] = "freelance"
    elif not hi and re.search(r"jusqu.à|up to|maximum|\bmax\b|bis zu", t[max(0, m.start() - 20):m.start()]):
        out["excluded"] = "cap_only"
    elif not period:
        out["excluded"] = "unknown_period"
    else:
        rate = next((int(r) / 100 for r in re.findall(r"(?<![\d-])(\d{2})\s*%(?!\s*(?:-|–|à|to|bis))", w) if int(r) >= 10), 1)
        months = 13 if re.search(r"13e|13th|13ème|13 mois|13\.? monat", t) else 12
        f = {"hour": hours * 52, "day": 260, "month": months, "year": 1}[period] / rate
        out["annual_min"], out["annual_max"] = round(lo * f), round((hi or lo) * f)
        b = seed("salary_bounds").get(cur)
        if hi and hi > 3 * lo:
            out["excluded"] = "range_too_wide"
        elif not b or not float(b["min_year"]) <= out["annual_min"] <= out["annual_max"] <= float(b["max_year"]):
            out["excluded"] = "out_of_bounds"
    return out


def to_eur(amount, currency):
    return round(amount * float(seed("fx_rates")[currency]["eur_per_unit"]))
