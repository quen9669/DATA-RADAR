# Roadmap Data Job Radar (22 nov. 2026)

## Règles
1. **Code minimaliste** : une fonction par méthode, partagée par toutes les sources. Une nouvelle source = une ligne de `sources.csv` (+ un modèle staging seulement si le format est nouveau). Supprimer avant d'ajouter. Plafond de 1 000 lignes mesuré par la CI.
2. **On prend tout** : toutes les offres de chaque site, sans filtre de métier ni de contrat, avec lien qui fonctionne et salaire min et max quand il existe.
3. **Un principal et un secours par source** : si la méthode principale échoue ou rend zéro offre, la suivante prend le relais dans le même run. Un run entièrement en échec ouvre une alerte.
4. **Brut complet** : la réponse entière de chaque site est enregistrée (description complète comprise). Si une liste tronque la description, on télécharge aussi la page de détail. Chaque source a un cas « description complète » dans `checks.md`.
5. **Un seul format ensuite** : bronze (brut Parquet), silver (un modèle par format, mêmes colonnes imposées par un test, puis `postings`), gold (`offers`, `salaries`, `source_ranking`, `health`). Silver et gold se refont depuis le bronze.
6. **Tout dans GitHub** : code, `sources.csv`, workflows, secrets. Claude ne lit jamais une clé. Les données restent sur R2 (plafond 9,95 Go).
7. **Comptes gratuits** : un compte par service pour commencer. Si besoin, comptes supplémentaires numérotés `_2`, `_3`, `_4`, l'adresse mail de référence étant notée par FRANKS ; ajoutés au fur et à mesure.

## Phases
| Phase | Contenu | État |
|---|---|---|
| 0. Sauver | Historique VPS vers Parquet sur R2 | fait |
| 1. Socle | `offers`, `health`, classement des sources | fait |
| 2. Salaires | `salary.py`, 95 % de précision, min et max partout | fait |
| 3. APIs | EURES LU, Job-Room CH, ADEM (Firecrawl), compaction. En attente : 7 jours sans trou, relecture des cas, plan Firecrawl, décision VPS (~13 déc.) | fusionnée, validation en attente |
| **4a. Quick wins** | Fonctions `page` et `jobspy`, sources ci-dessous, Luxembourg d'abord | à faire |
| 4b. Le reste | jobs.ch, jobup.ch, LinkedIn, grands employeurs (ATS), institutions européennes, secours payants | plus tard |
| 5. Compétences | Seed `skills`, liste par offre | plus tard |
| 6. Monitoring | Page statique : offres par jour et par source, % avec salaire, jobs en échec | plus tard |

## Phase 4a : sources (principal → secours)
Volumes tirés d'une analyse externe, non vérifiés : à mesurer au premier run.

| Source | Méthode | Ce qu'on prend |
|---|---|---|
| Indeed LU | `jobspy` → `apify` | tout, requêtes multiples pour passer le plafond de 1 000 résultats |
| Google Jobs LU | `jobspy` → `serpapi` | tout |
| GovJobs (État, communes) | `page` → `firecrawl` | ~250 offres, groupe A1 à C2 |
| Moovijob | `page` → `firecrawl` | toutes les offres, tous contrats, sans filtre |
| jobs.lu | `page` → `firecrawl` | ~1 186 offres |
| Jobfinder.lu | `page` → `firecrawl` | ~354 offres |
| Freelancers.lu, LuxFreelance.lu | `page` → `firecrawl` | missions freelance (~47) |
| TED (marchés publics) | `api` → `firecrawl` | appels d'offres IT et conseil au LU, table à part |
| EURES Suisse | `api` → `firecrawl` | ajouter `ch` aux codes de lieu |
| Salaire min/max structuré | dbt | un modèle commun lit le `baseSalary` des pages `JobPosting` |
| Liens qui fonctionnent | `check` | code HTTP de chaque lien ; lien mort = offre retirée |

Pour chaque source : 5 cas dans `checks.md`, un test, `dbt build` vert avant commit.

## Plus tard (4b)
LinkedIn (proxies ou Apify payant), jobs.ch, jobup.ch, grands employeurs (ATS), ICTjob, Nexten, Paperjam, eFinancialCareers, BEI, NSPA, LIST (30 minutes d'inspection réseau avant de coder), Optioncarriere.lu.

## Écartées
Monster.lu, Glassdoor, ZipRecruiter, 100 sites communaux, page publique ADEM (déjà couverte par Firecrawl).

## Risques
- CGU de plusieurs sites interdisant le scraping : risque accepté, données privées, jamais republiées.
- IP de GitHub bloquées : `firecrawl` en secours (1 000 pages/mois gratuites, ADEM en consomme ~330).
- Bucket R2 sous 9,95 Go : compaction mensuelle.
