-- jobs.lu (LU): the detail page is plain HTML; the "Payment" line is kept in the description so that salary.py reads it.
with page as (
    select item_id, first_seen, last_seen, coalesce(json_extract_string(try_cast(body as json), '$.data.rawHtml'), body) as html
    from {{ raw('jobs_lu') }} where item_id like '%ApplyForJob.aspx?Id=%'
), f as (
    select *, regexp_extract(html, '(?s)<dt>\s*Payment:\s*</dt>\s*<dd>(.*?)</dd>', 1) as payment from page
)
select
    'jobs_lu' as source_id,
    regexp_extract(item_id, 'Id=(\d+)', 1) as source_item_id,
    trim(regexp_extract(html, '(?s)<h1 class="job-title">(.*?)</h1>', 1)) as title,
    trim(regexp_extract(html, '(?s)<dd class="company-name">(.*?)</dd>', 1)) as company,
    'LU' as country,
    trim(regexp_extract(html, '(?s)<dt>\s*Location:\s*</dt>\s*<dd>(.*?)</dd>', 1)) as city,
    try_strptime(trim(regexp_extract(html, '(?s)<dt>\s*Last updated:\s*</dt>\s*<dd>(.*?)</dd>', 1)), '%d %B %Y')::date as published_on,
    'Payment: ' || trim(payment) || '. ' || regexp_replace(regexp_extract(html, '(?s)job-html-description">(.*?)</div>', 1), '<[^>]+>', ' ', 'g') as description,
    item_id as url,
    first_seen, last_seen
from f
