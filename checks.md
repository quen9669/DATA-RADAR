# Cas de validation manuelle (Phase 3)

Pour chaque source : ouvrir l'offre sur le site, comparer avec la colonne « Attendu ». Candidats tirés de `check_cases` (build du 21 nov. 2026). Les textes allemands sont traduits en français ; l'original est entre guillemets.

Cas : 1 salaire en champ dédié · 2 salaire dans le texte · 3 mensuel avec 13e mois ou temps partiel · 4 mission freelance (TJM) · 5 sans salaire puis retirée.

Limites connues : aucune des trois sources n'a de champ salaire structuré (cas 1 sans objet) ; le retrait d'une offre n'est pas détecté (cas 5 : seule la première moitié, « salaire vide », est vérifiable).

## eures (Luxembourg)

| Cas | Offre | Attendu | Observé |
|---|---|---|---|
| 1 | — | sans objet : pas de champ salaire | — |
| 2 | `eures:MTA0NjM4IDEx` Comptable immobilier (h/f) | « EUR 60K - 80K per year » → 60 000 à 80 000 € annuel | 60 000 € (OK) |
| 2 bis | `eures:MTA1NTE1IDEx` Market Head for Central and Northern Europe | « pay range €200,000 – €350,000 » | 200 000 € (OK) |
| 3 | `eures:MTA1NTc1IDEx` Postdoctoral researcher (carbon fibre) | « salaire mensuel brut entre 6 094 € et 6 678 €, versé sur 13 mois » → annuel 79 222 à 86 814 € | `annual_min_eur` = 6 094 : **à contrôler** (le 13e mois et l'annualisation semblent ignorés dans ce modèle) |
| 4 | `eures:MTA3NDA0IDEx` Office & Administration Officer | aucune mission freelance : le texte parle de « chèque-repas 13,5 € / jour » | classée « freelance » à tort (faux positif sur « / jour ») |
| 5 | `eures:MTA0MDA1IDEx` (Head of Group Financial Crime Compliance & Group MLRO) | aucun salaire dans l'annonce ; retrait à vérifier plus tard | salaire vide (OK), retrait non détecté |

## job_room (Suisse, secondaire)

| Cas | Offre | Attendu | Observé |
|---|---|---|---|
| 1 | — | sans objet | — |
| 2 | `job_room:05510041-7356-4ff4-9671-5d49bda8c3f2` Chef d'équipe planification de production (« Teamleiter:in Produktionsplanung ») | « Fourchette de salaire CHF 92'000 – 100'000 » | 98 440 € min, soit 92 000 CHF × 1,07 (OK) |
| 3 | `job_room:37ba4500-285c-40b2-ae51-2cffb491d4dc` Collaborateur de vente 100 % (« Mitarbeiter:in Verkauf 100% (Frühschicht) ») | « salaire d'entrée CHF 4'200 plus 13e mois » → 54 600 CHF annuel | 4 494 € : **à contrôler** (13e mois non appliqué) |
| 3 bis | `job_room:6202e6ef-522d-43dc-8cfd-8a9db23ee588` Cleaning Agent | « CHF 1108 brut par mois pour 12 à 13 heures » → temps partiel, à annualiser et ramener au temps plein | 1 186 € : **à contrôler** (temps partiel ignoré) |
| 4 | `job_room:1a76ea02-e3ae-4180-8fb9-72e660e6a156` Recruiter | pas une mission : « salaire entre CHF 85'000 et 95'000 », hybride « 2 jours par semaine » | classée « freelance » à tort (faux positif sur « jours par semaine ») |
| 5 | `job_room:0019ad59-8eff-4ab8-b24c-9f22c6956b6c` Spécialiste en excellence opérationnelle | aucun salaire | vide (OK), retrait non détecté |
| anomalie | `job_room:133db9bf-6b5d-4d12-b750-7ae0adf128b2` Sales Consultant Swisscom Shop Zurich | « salaire horaire fixe de 33,44 CHF brut, 40 h/semaine » → ≈ 74 000 CHF annuel | `annual_min_eur` = 36 : **bug** (taux horaire non annualisé) |

## adem (Luxembourg)

| Cas | Offre | Attendu | Observé |
|---|---|---|---|
| 1 | — | sans objet | — |
| 2 | aucune offre avec salaire dans les 21 offres collectées (0 salaire sur 2 780 offres historiques) | — | à chercher dans les prochains jours |
| 3 | idem | — | — |
| 4 | idem | — | — |
| 5 | `adem:…/assistant-administratif-m-f-803754.html` et `…/agent-de-restauration-plonge-m-f-x-cdi-40h-semaine-803738.html` | aucun salaire ; retrait à vérifier plus tard | vide (OK), retrait non détecté |

## Correctifs appliqués après ce tableau
Les colonnes « Observé » ci-dessus datent du build avant correctif. Corrigés ensuite (avec 4 cas ajoutés aux tests) : montants en € (le modèle convertissait le montant de la période, pas l'annuel : 6 094 devient 79 222, 33,44 CHF/h devient 69 555 CHF, 1 108 CHF/mois à 13 h devient 40 911 CHF) ; « chèque-repas / jour » n'est plus lu comme salaire ; « 2 jours par semaine » ne force plus la période « jour » quand le montant est annuel. Le prochain build donnera les valeurs à comparer.

## À décider par FRANKS
- Les cas 2, 3, 4 d'ADEM faute de données : accepter « 0 salaire sur ADEM » comme cas validé, ou attendre une offre avec salaire ?

## Phase 4a (govjobs, jobs_lu, moovijob, luxsearch, jobfinder, indeed_lu) : cas à remplir après le premier run
Mêmes 5 cas par source. Les candidats viendront de `check_cases` une fois les données collectées ; tant que les URL de liste et les motifs de liens de `sources.csv` ne sont pas confirmés par `python radar.py check`, aucune offre n'est validée. Cas 1 (salaire structuré) : `baseSalary` JSON-LD pour les 4 sites `page`, champs `min_amount`/`max_amount` pour indeed_lu.
