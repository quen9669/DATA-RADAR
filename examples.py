import json, os, sys
import duckdb
sys.path.insert(0, ".")
import radar
r2 = radar.connect()
r2.execute("ATTACH 'dbt/radar.duckdb' AS radar (READ_ONLY)")
r2.execute("USE radar")
db = r2
bucket = radar.BUCKET
print("STATS", json.dumps(db.execute("""select p.source_id, count(*) n, count(title) titles, count(company) companies, count(description) descs,
    avg(length(description))::int avg_desc, count(distinct s.offer_id) with_salary from postings p left join salaries s using (offer_id) group by 1 order by 1""").fetchall(), default=str))
for source in ["indeed_lu", "jobs_lu", "jobfinder", "moovijob", "govjobs", "eures", "job_room", "adem"]:
    row = db.execute("""select offer_id, source_id, source_item_id, title, company, city, country, published_on, url, length(description), description,
        salary_min, salary_max, salary_currency from postings where source_id = ? and title is not null and length(description) > 300
        order by md5(offer_id) limit 1""", [source]).fetchone()
    if not row:
        print("EX", json.dumps({"source": source, "none": True}))
        continue
    cols = ["offer_id", "source_id", "source_item_id", "title", "company", "city", "country", "published_on", "url", "desc_len", "description",
            "salary_min", "salary_max", "salary_currency"]
    silver = dict(zip(cols, row))
    gold = db.execute("select origin, salary_eur_min, salary_eur_max from salaries where offer_id = ?", [row[0]]).fetchall()
    bronze = r2.execute(f"""select item_id, method, length(body), left(body, 1800), fetched_at from read_parquet('r2://{bucket}/raw/source={source}/*/*.parquet')
        where item_id in (?, ?) limit 1""", [row[2], row[8]]).fetchone()
    silver["description"] = silver["description"][:1500]
    print("EX", json.dumps({"source": source, "silver": silver, "gold": gold, "bronze": bronze}, default=str, ensure_ascii=False))
