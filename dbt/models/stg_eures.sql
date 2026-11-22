-- EURES (LU): one row per vacancy, latest version.
with jv as (select item_id, first_seen, last_seen, body::json as j from {{ raw('eures') }})
select
    'eures' as source_id,
    item_id as source_item_id,
    json_extract_string(j, '$.title') as title,
    json_extract_string(j, '$.employer.name') as company,
    'LU' as country,
    json_extract_string(j, '$.locationMap.LU[0]') as city,
    cast(to_timestamp(try_cast(json_extract(j, '$.creationDate') as bigint) / 1000) as date) as published_on,
    json_extract_string(j, '$.description') as description,
    null as url,
    first_seen,
    last_seen
from jv
