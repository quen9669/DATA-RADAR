import os
import sys

import pandas as pd

sys.path.insert(0, os.path.abspath(".."))
from salary import parse, to_eur  # noqa: E402


def model(dbt, session):
    dbt.config(materialized="table")
    rows = []
    for offer_id, source_id, description in dbt.ref("stg_descriptions").fetchall():
        p = parse(description)
        if p:
            eur = {k: to_eur(p[k], p["currency"]) if p["annual_" + k[:3]] and p["currency"] in ("EUR", "CHF") else None
                   for k in ("min", "max")}
            rows.append({"offer_id": offer_id, "source_id": source_id, **p, "annual_min_eur": eur["min"], "annual_max_eur": eur["max"]})
    return pd.DataFrame(rows)
