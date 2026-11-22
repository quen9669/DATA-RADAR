-- Every annual gross full-time salary in EUR, legacy and collected since phase 3, as min and max (no range: min = max).
select offer_id::varchar as offer_id, 'legacy' as origin, salary_eur_min, salary_eur_max from {{ ref('offers') }} where has_salary
union all
select offer_id, 'text', annual_min_eur, coalesce(annual_max_eur, annual_min_eur) from {{ ref('salary_text') }}
where excluded is null and annual_min_eur is not null
union all
select p.offer_id, 'structured', round(p.salary_min * fx.eur_per_unit), round(p.salary_max * fx.eur_per_unit)
from {{ ref('postings') }} p join {{ ref('fx_rates') }} fx on fx.currency = p.salary_currency where p.salary_min > 0
