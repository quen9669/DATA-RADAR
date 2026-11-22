-- Indeed Luxembourg (JobSpy): one row per ad; the salary fields are structured.
with ad as (select item_id, first_seen, last_seen, body::json as j from {{ raw('indeed_lu') }})
select
    'indeed_lu' as source_id,
    item_id as source_item_id,
    json_extract_string(j, '$.title') as title,
    json_extract_string(j, '$.company') as company,
    'LU' as country,
    json_extract_string(j, '$.location') as city,
    try_cast(left(json_extract_string(j, '$.date_posted'), 10) as date) as published_on,
    json_extract_string(j, '$.description') as description,
    json_extract_string(j, '$.job_url') as url,
    case json_extract_string(j, '$.interval') when 'yearly' then try_cast(json_extract_string(j, '$.min_amount') as double)
        when 'monthly' then try_cast(json_extract_string(j, '$.min_amount') as double) * 12 end as salary_min,
    case json_extract_string(j, '$.interval') when 'yearly' then coalesce(try_cast(json_extract_string(j, '$.max_amount') as double), try_cast(json_extract_string(j, '$.min_amount') as double))
        when 'monthly' then coalesce(try_cast(json_extract_string(j, '$.max_amount') as double), try_cast(json_extract_string(j, '$.min_amount') as double)) * 12 end as salary_max,
    upper(json_extract_string(j, '$.currency')) as salary_currency,
    first_seen,
    last_seen
from ad
