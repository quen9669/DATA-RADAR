# Data Job Radar

Offres d'emploi et salaires LU/CH : récupérer le maximum, avec le moins de code. Python (stdlib) + DuckDB + dbt + JobSpy. GitHub Actions collecte ; brut en Parquet sur R2.

## Doctrine
- 1 000 lignes max (Python, SQL, YAML, tests, CI ; seeds exclus), vérifié par la CI. Chaque ligne : minimale, facile à maintenir, fiable.
- Supprimer avant d'ajouter. Une fonction par méthode (`api`, `page`, `ats`, `jobspy`, `firecrawl`, `apify`, `serpapi`), partagée par toutes les sources.
- Chaque source : une méthode principale, au moins un secours. Nouvelle source = une ligne de `sources.csv` + un modèle staging + 5 cas dans `checks.md`.
- Python sauvegarde la réponse brute entière ; tout le parsing est en dbt. Aucune information perdue (compaction = versions distinctes gardées).
- Salaire : champ structuré d'abord, sinon `salary.py`. Une estimation n'est jamais un salaire employeur.
- Une règle métier = une ligne de seed CSV. Exclure n'est pas supprimer.
- Logique non triviale = un test. `dbt build` vert avant commit.
- Gratuit d'abord ; payant seulement sans alternative. Bucket sous 9,95 Go.

## Secrets
Dans les secrets GitHub uniquement. Claude passe par les workflows, ne lit, n'affiche ni ne demande jamais une clé.

## Commandes
`python radar.py [source]` · `python radar.py check` · `dbt build` · `python -m unittest`

Réponses en français, code en anglais. Le résultat d'abord.
