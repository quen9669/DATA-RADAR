-- Jobfinder.lu (LU): the vacancy is the JSON of the page's __NEXT_DATA__ (title and description are HTML, in en, fr, de or lb). The city is the employer's address.
with page as (
    select item_id, first_seen, last_seen, coalesce(json_extract_string(try_cast(body as json), '$.data.rawHtml'), body) as html
    from {{ raw('jobfinder') }} where regexp_matches(item_id, '/jobs/[0-9a-f]{24}$')
), d as (
    select *, regexp_extract(html, '(?s)__NEXT_DATA__[^>]*>(.*?)</script>', 1)::json as nd from page
), j as (
    select *, json_extract(nd, '$.props.pageProps.dehydratedState.queries[0].state.data') as o from d
)
select
    'jobfinder' as source_id,
    regexp_extract(item_id, '([0-9a-f]{24})$', 1) as source_item_id,
    coalesce(json_extract_string(o, '$.offer.job.title.en'), json_extract_string(o, '$.offer.job.title.fr'), json_extract_string(o, '$.offer.job.title.de'), json_extract_string(o, '$.offer.job.title.lb')) as title,
    json_extract_string(o, '$.company.name') as company,
    'LU' as country,
    json_extract_string(o, '$.company.contact.address.city') as city,
    try_cast(left(json_extract_string(o, '$.offer.visible_online'), 10) as date) as published_on,
    regexp_replace(coalesce(json_extract_string(o, '$.offer.job.description.en'), json_extract_string(o, '$.offer.job.description.fr'), json_extract_string(o, '$.offer.job.description.de'), json_extract_string(o, '$.offer.job.description.lb')), '<[^>]+>', ' ', 'g') as description,
    item_id as url,
    first_seen, last_seen
from j
