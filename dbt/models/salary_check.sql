-- salary.py against the legacy parser, per source: how often do both agree within 1 %?
select
    t.source_id,
    count(*) as parsed,
    count(*) filter (where t.excluded is null) as kept,
    count(*) filter (where t.excluded is null and s.annuel_brut_tp_eur_point is not null
        and abs(s.annuel_brut_tp_eur_point - (t.annual_min_eur + t.annual_max_eur) / 2) <= 0.01 * s.annuel_brut_tp_eur_point) as agree,
    count(*) filter (where t.excluded is null and s.annuel_brut_tp_eur_point is null) as new_only,
    count(*) filter (where t.excluded is not null and s.compte_comme_observe) as legacy_only
from {{ ref('salary_text') }} t
left join {{ legacy('core/offre_salaire') }} s on s.offre_id = t.offer_id
group by 1 order by 2 desc
