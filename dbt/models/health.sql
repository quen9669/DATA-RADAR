-- One row per source: volume, freshness, salary coverage, last run outcome.
with last_run as (
    select source_id, debut, statut from {{ legacy('core/run') }}
    qualify row_number() over (partition by source_id order by debut desc) = 1
)
select
    s.source_id,
    s.etat_collecte as collect_state,
    r.offers,
    r.offers_with_salary,
    r.salary_pct,
    r.rank as salary_rank,
    max(os.vue_derniere_fois) as last_seen,
    count(*) filter (where os.etat = 'quarantaine') as quarantined,
    l.debut as last_run_at,
    l.statut as last_run_status
from {{ legacy('core/source') }} s
left join {{ ref('source_ranking') }} r using (source_id)
left join {{ legacy('core/offre_source') }} os using (source_id)
left join last_run l using (source_id)
group by all
