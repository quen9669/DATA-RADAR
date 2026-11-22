-- One row per unique offer; salary only if employer-published and counted as observed.
with src as (
    select offre_id, list(distinct source_id order by source_id) as sources
    from {{ legacy('core/offre_source') }} where offre_id is not null group by 1
)
select
    o.offre_id as offer_id,
    o.etat as status,
    o.intitule_brut as title,
    o.pays as country,
    o.ville as city,
    o.entreprise_id as company_id,
    o.date_publication as published_on,
    o.vue_premiere_fois as first_seen,
    o.vue_derniere_fois as last_seen,
    src.sources,
    s.annuel_brut_tp_eur_point as salary_eur_year,
    s.annuel_brut_tp_min as salary_min,
    s.annuel_brut_tp_max as salary_max,
    coalesce(case when s.annuel_brut_tp_eur_point is not null then round(s.annuel_brut_tp_eur_point * coalesce(s.annuel_brut_tp_min, s.annuel_brut_tp_max)
        / ((coalesce(s.annuel_brut_tp_min, s.annuel_brut_tp_max) + coalesce(s.annuel_brut_tp_max, s.annuel_brut_tp_min)) / 2)) end, s.annuel_brut_tp_eur_point) as salary_eur_min,
    coalesce(case when s.annuel_brut_tp_eur_point is not null then round(s.annuel_brut_tp_eur_point * coalesce(s.annuel_brut_tp_max, s.annuel_brut_tp_min)
        / ((coalesce(s.annuel_brut_tp_min, s.annuel_brut_tp_max) + coalesce(s.annuel_brut_tp_max, s.annuel_brut_tp_min)) / 2)) end, s.annuel_brut_tp_eur_point) as salary_eur_max,
    s.devise as salary_currency,
    s.salaire_origine as salary_origin,
    s.motif_exclusion as salary_excluded_reason,
    coalesce(s.compte_comme_observe, false) and s.annuel_brut_tp_eur_point is not null as has_salary
from {{ legacy('core/offre') }} o
left join src using (offre_id)
left join {{ legacy('core/offre_salaire') }} s using (offre_id)
