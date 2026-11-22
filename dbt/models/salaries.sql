-- Every annual gross full-time salary in EUR, legacy and collected since phase 3, as min and max (no range: min = max).
select offer_id::varchar as offer_id, 'legacy' as origin, salary_eur_min, salary_eur_max from {{ ref('offers') }} where has_salary
union all
select offer_id, 'text', annual_min_eur, coalesce(annual_max_eur, annual_min_eur) from {{ ref('salary_text') }}
where excluded is null and annual_min_eur is not null
