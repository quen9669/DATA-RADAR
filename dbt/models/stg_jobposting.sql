-- Every `page` source that publishes the schema.org JobPosting (JSON-LD) of a detail page, read from the raw page or from Firecrawl's rawHtml. Salary is structured.
{% set sources = ['govjobs', 'moovijob'] %}
with page as (
    {% for s in sources %}select '{{ s }}' as source_id, * from {{ raw(s) }}{{ ' union all ' if not loop.last }}{% endfor %}
), h as (
    select *, coalesce(json_extract_string(try_cast(body as json), '$.data.rawHtml'), body) as html from page
), ld as (
    select source_id, item_id, first_seen, last_seen, html,
        try_cast(list_filter(regexp_extract_all(html,
            '(?s)<script[^>]*ld\+json[^>]*>(.*?)</script>', 1), lambda x: x like '%"JobPosting"%')[1] as json) as j
    from h
), pay as (
    select *, upper(coalesce(json_extract_string(j, '$.baseSalary.value.unitText'), json_extract_string(j, '$.baseSalary.unitText'))) as unit,
        coalesce(try_cast(json_extract_string(j, '$.baseSalary.value.minValue') as double), try_cast(json_extract_string(j, '$.baseSalary.value.value') as double),
            try_cast(json_extract_string(j, '$.baseSalary.value') as double)) as lo,
        try_cast(json_extract_string(j, '$.baseSalary.value.maxValue') as double) as hi
    from ld where j is not null
)
select
    source_id, item_id as source_item_id,
    json_extract_string(j, '$.title') as title,
    json_extract_string(j, '$.hiringOrganization.name') as company,
    'LU' as country,
    coalesce(json_extract_string(j, '$.jobLocation.address.addressLocality'), json_extract_string(j, '$.jobLocation[0].address.addressLocality')) as city,
    try_cast(left(json_extract_string(j, '$.datePosted'), 10) as date) as published_on,
    coalesce('Salaire : ' || nullif(regexp_extract(html, '(?s)Entre\s+(\d+\s*k?\s+et\s+\d+\s*k?)\s*€', 1), '') || ' €. ', '') || regexp_replace(json_extract_string(j, '$.description'), '<[^>]+>', ' ', 'g') as description,
    item_id as url,
    case unit when 'YEAR' then lo when 'MONTH' then lo * 12 end as salary_min,
    case unit when 'YEAR' then coalesce(hi, lo) when 'MONTH' then coalesce(hi, lo) * 12 end as salary_max,
    json_extract_string(j, '$.baseSalary.currency') as salary_currency,
    first_seen, last_seen
from pay
