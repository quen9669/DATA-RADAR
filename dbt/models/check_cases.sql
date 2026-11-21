-- Candidates for the manual checks (checks.md): two offers per source and case, to compare with the site.
with cases as (
    select p.source_id, p.offer_id, p.title, p.url,
        case when t.offer_id is null then '5 sans salaire' when t.excluded = 'freelance' then '4 freelance'
             when t.excluded is not null then '0 exclu' when t.period = 'month' then '3 mensuel' else '2 texte annuel' end as kind,
        t.annual_min_eur, left(t.context, 160) as context
    from {{ ref('postings') }} p left join {{ ref('salary_text') }} t using (offer_id)
)
select * from cases qualify row_number() over (partition by source_id, kind order by offer_id) <= 2 and kind <> '0 exclu'
order by source_id, kind
