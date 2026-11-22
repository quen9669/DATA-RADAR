-- Job-Room (CH): one row per ad, latest version. Salary has no structured field: it comes from the text.
with ad as (select item_id, first_seen, last_seen, body::json as j from {{ raw('job_room') }})
select
    'job_room' as source_id,
    item_id as source_item_id,
    json_extract_string(j, '$.jobAdvertisement.jobContent.jobDescriptions[0].title') as title,
    json_extract_string(j, '$.jobAdvertisement.jobContent.company.name') as company,
    json_extract_string(j, '$.jobAdvertisement.jobContent.location.countryIsoCode') as country,
    json_extract_string(j, '$.jobAdvertisement.jobContent.location.city') as city,
    try_cast(json_extract_string(j, '$.jobAdvertisement.publication.startDate') as date) as published_on,
    json_extract_string(j, '$.jobAdvertisement.jobContent.jobDescriptions[0].description') as description,
    json_extract_string(j, '$.jobAdvertisement.jobContent.externalUrl') as url,
    first_seen,
    last_seen
from ad
