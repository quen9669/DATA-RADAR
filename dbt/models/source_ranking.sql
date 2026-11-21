-- Sources ranked by distinct offers carrying an employer salary.
select
    row_number() over (order by count(distinct o.offer_id) filter (where o.has_salary) desc, os.source_id) as rank,
    os.source_id,
    count(distinct o.offer_id) as offers,
    count(distinct o.offer_id) filter (where o.has_salary) as offers_with_salary,
    round(100.0 * offers_with_salary / offers, 2) as salary_pct
from {{ legacy('core/offre_source') }} os
join {{ ref('offers') }} o on o.offer_id = os.offre_id
group by os.source_id
