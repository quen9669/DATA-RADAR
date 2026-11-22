import json, re, sys
sys.path.insert(0, ".")
import radar
src = {"url": "", "fallback_url": ""}


def get(url, method="page"):
    t = radar.METHODS[method](src, 0, url)
    return json.loads(t)["data"]["rawHtml"] if method == "firecrawl" else t


def flat(o, p="", out=None):
    out = {} if out is None else out
    if isinstance(o, dict):
        for k, v in o.items():
            flat(v, f"{p}.{k}", out)
    elif isinstance(o, list):
        for i, v in enumerate(o[:2]):
            flat(v, f"{p}[{i}]", out)
    else:
        out[p] = str(o)[:80]
    return out


t = get("https://www.jobfinder.lu/jobs/6992c307a881c273d79efe01")
nd = json.loads(re.search(r"__NEXT_DATA__[^>]*>(.*?)</script>", t, re.S).group(1))
print("## JOBFINDER", json.dumps(flat(nd["props"]["pageProps"]["dehydratedState"]["queries"][0]["state"]["data"]), ensure_ascii=False)[:3500])
t = get("https://en.jobs.lu/Jobs.aspx")
i = t.find("ApplyForJob.aspx?Id=")
print("## JOBSLU LIST", re.sub(r"\s+", " ", t[i - 600:i + 1200]))
t = get("https://en.jobs.lu/ApplyForJob.aspx?Id=291682")
i = t.find("job-details-header")
print("## JOBSLU DETAIL", re.sub(r"\s+", " ", t[i - 100:i + 1800]))
i = t.find("job-html-description")
print("## JOBSLU DESC", re.sub(r"\s+", " ", t[i:i + 700]))
t = get("https://www.moovijob.com/offres-emploi/cbl-sa/conducteur-principal-gros-oeuvre", "firecrawl")
print("## MOOVIJOB LD", re.findall(r'<script[^>]*ld\+json[^>]*>(.*?)</script>', t, re.S)[0][:3000])
t = get("https://govjobs.public.lu/fr/postuler/postes-ouverts.html")
print("## GOV SCRIPTS", re.findall(r'(?:src|data-[a-z-]*url|action)="([^"]+)"', t)[:30])
i = t.find("Découvrez ci-dessous")
print("## GOV BODY", re.sub(r"\s+", " ", t[i:i + 2500]))
