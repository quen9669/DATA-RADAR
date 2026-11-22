-- ADEM (LU): the vacancy is a JSON object embedded in the detail page (Firecrawl output); the listing page is not an offer.
with page as (
    select item_id, first_seen, last_seen, replace(json_extract_string(body::json, '$.data.rawHtml'), '&quot;', '"') as html
    from {{ raw('adem') }} where item_id like '%/jobboard/offre/%'
), offer as (
    select *, regexp_extract(html, '"offer":(\{[^{}]*\})', 1)::json as j from page
)
select
    'adem' as source_id,
    item_id as source_item_id,
    json_extract_string(j, '$.title') as title,
    json_extract_string(j, '$.employer') as company,
    'LU' as country,
    json_extract_string(j, '$.commune') as city,
    try_cast(json_extract_string(j, '$.publicationDate') as date) as published_on,
    regexp_replace(regexp_replace(substr(html, instr(html, 'jobboard-offer-main')), '^jobboard-offer-main[^>]*>', ''), '<[^>]+>', ' ', 'g') as description,
    item_id as url,
    first_seen,
    last_seen
from offer
