-- Candidates for the manual checks (checks.md): two offers per source and case, to compare with the site.
with cases as (
    select p.source_id, p.offer_id, p.title,
        case p.source_id when 'eures' then 'https://europa.eu/eures/portal/jv-se/jv-details/' || p.source_item_id || '?lang=fr'
             when 'job_room' then 'https://www.job-room.ch/job-search/' || p.source_item_id else p.url end as link,
        case when t.offer_id is null then '5 sans salaire' when t.excluded = 'freelance' then '4 freelance'
             when t.excluded is not null then '0 exclu' when t.period = 'month' then '3 mensuel' else '2 texte annuel' end as kind,
        t.annual_min_eur, coalesce(t.annual_max_eur, t.annual_min_eur) as annual_max_eur, left(t.context, 160) as context
    from {{ ref('postings') }} p left join {{ ref('salary_text') }} t using (offer_id)
)
select * from cases qualify row_number() over (partition by source_id, kind order by offer_id) <= 2 and kind <> '0 exclu'
order by source_id, kind
