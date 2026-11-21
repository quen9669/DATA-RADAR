"""Salary text -> annual gross full-time amount. Pure stdlib; seeds hold the rules."""
import csv, pathlib, re

SEEDS = pathlib.Path(__file__).parent / "dbt" / "seeds"
CUR = r"(chf|sfr|fr\.|€|eur(?:os?)?\b|\$|usd|£|gbp)"
NUM = r"(\d+[.,]\d{4}(?!\d)|\d{1,3}(?:[ '’.,\u202f\u00a0]\d{3})+(?:[.,]\d{1,2})?|\d+(?:[.,]\d{1,2})?)\s*(k\b)?"
SEP = r"(?:-|–|—|à|to|bis|et|und|and)"
AMOUNT = re.compile(rf"(?:{CUR}\s*)?{NUM}\s*{CUR}?(?:\s*{SEP}\s*(?:{CUR}\s*)?{NUM}\s*{CUR}?)?", re.I)
KEY = re.compile(r"salaire|salary|r[ée]mun[ée]ration|gehalt|lohn|verg[üu]tung|brut|gross|package|compensation|pay\b|payment")
PERIODS = [("hour", r"/\s*h\b|heure|per hour|hourly|stunde"), ("day", r"/\s*j\b|jour|per day|daily|tag\b|tagessatz"),
           ("month", r"mois|month|monat|mensuel"), ("year", r"/\s*an|\ban\b|année|year|annuel|annual|jahr|p\.a\.|per annum|/\s*a\b")]
CODES = {"€": "EUR", "eur": "EUR", "euro": "EUR", "euros": "EUR", "$": "USD", "usd": "USD", "£": "GBP", "gbp": "GBP"}


def seed(name):
    with open(SEEDS / f"{name}.csv", newline="") as f:
        return {r["currency"]: r for r in csv.DictReader(f)}


def num(s, k):
    s = re.sub(r"[ '’\u202f\u00a0]", "", s)
    if "." in s and "," in s:  # the last separator is the decimal one
        dec = max(s.rfind("."), s.rfind(","))
        s = re.sub(r"[.,]", "", s[:dec]) + "." + s[dec + 1:]
    else:
        s = re.sub(r"[.,]", "", s) if re.fullmatch(r"\d{1,3}([.,]\d{3})+", s) else s.replace(",", ".")
    return float(s) * (1000 if k else 1)


def first(periods, text):
    """Period whose marker appears earliest in text."""
    found = [(m.start(), p) for p, rx in periods if (m := re.search(rx, text))]
    return min(found)[1] if found else None


def variable(before):
    """True when a commission/bonus word precedes the amount with no salary word in between."""
    hits = list(re.finditer(r"provision|commission|\bote\b|bonus|prämie|prime", before))
    return bool(hits) and not KEY.search(before[hits[-1].end():]) and not re.search(r"exclud|hors |ohne|sans ", before)


def parse(text, hours=40.0):
    """First amount that looks like a salary -> dict(min, max, currency, period, context, annual_min, annual_max, excluded), else None."""
    t = text.lower().replace("\\", "")
    for m in AMOUNT.finditer(t):
        c1, a, k1, c2, c3, b, k2, c4 = m.groups()
        cur = next((c for c in (c1, c2, c3, c4) if c), None)
        after = t[m.end():m.end() + 30]
        if cur and (KEY.search(t[max(0, m.start() - 60):m.start()]) or first(PERIODS, after)):
            try:
                lo, hi = num(a, k1), num(b, k2 or k1) if b else None
            except ValueError:  # e.g. "2.910.00": not an amount
                continue
            break
    else:
        return None
    if hi and k2 and not k1 and lo < 1000:
        lo *= 1000
    cur = CODES.get(cur, "CHF" if cur in ("chf", "sfr", "fr.") else cur.upper())
    w = t[max(0, m.start() - 80):m.end() + 120]
    bounds = seed("salary_bounds").get(cur)
    period = first(PERIODS, after) or first(PERIODS, w)
    if not period and bounds and lo >= float(bounds["infer_year_from"]):
        period = "year"
    out = dict(min=lo, max=hi or lo, currency=cur, period=period, context=text[max(0, m.start() - 120):m.end() + 80],
               annual_min=None, annual_max=None, excluded=None)
    if re.search(r"\bnet\b|netto", w[:140]):
        out["excluded"] = "net"
    elif period == "day" or re.search(r"tjm|freelance|taux journalier|tagessatz|daily rate", w):
        out["excluded"] = "freelance"
    elif variable(t[max(0, m.start() - 70):m.start()]):
        out["excluded"] = "variable"
    elif not hi and re.search(r"jusqu.à|up to|maximum|\bmax\b|bis zu|atteindre", t[max(0, m.start() - 40):m.start()]):
        out["excluded"] = "cap_only"
    elif not period:
        out["excluded"] = "unknown_period"
    else:
        rate = next((int(r) / 100 for r in re.findall(r"(?<![\d–-])\b(\d{2})\s*%(?!\s*(?:-|–|à|to|bis))", after) if int(r) >= 10), 1)
        weekly = re.search(r"(\d{2})\s*(?:heures par semaine|h ?/ ?(?:sem|week)|hours? per week|stunden pro woche)", w)
        if weekly and period != "hour" and int(weekly[1]) < hours:
            rate = int(weekly[1]) / hours
        months = 13 if re.search(r"13e|13th|13ème|13 mois|13 months|13\.? monat", t) else 12
        f = {"hour": hours * 52, "day": 260, "month": months, "year": 1}[period] / rate
        out["annual_min"], out["annual_max"] = round(lo * f), round((hi or lo) * f)
        top = hi or lo
        if hi and hi > 3 * lo:
            out["excluded"] = "range_too_wide"
        elif not bounds or not (float(bounds["min_year"]) <= out["annual_min"] <= out["annual_max"] <= float(bounds["max_year"])) \
                or (period == "hour" and not float(bounds["min_hour"]) <= lo <= top <= float(bounds["max_hour"])):
            out["excluded"] = "out_of_bounds"
    return out


def to_eur(amount, currency):
    return round(amount * float(seed("fx_rates")[currency]["eur_per_unit"]))
