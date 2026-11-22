-- Offers collected since phase 3, one row per posting across sources. Text is decoded (HTML entities) and on one line; the raw keeps everything.
with u as (
    select source_id || ':' || source_item_id as offer_id, * from {{ ref('stg_job_room') }}
    union all by name
    select source_id || ':' || source_item_id as offer_id, * from {{ ref('stg_eures') }}
    union all by name
    select source_id || ':' || source_item_id as offer_id, * from {{ ref('stg_adem') }}
    union all by name
    select source_id || ':' || source_item_id as offer_id, * from {{ ref('stg_jobposting') }}
    union all by name
    select source_id || ':' || source_item_id as offer_id, * from {{ ref('stg_indeed_lu') }}
    union all by name
    select source_id || ':' || source_item_id as offer_id, * from {{ ref('stg_jobs_lu') }}
    union all by name
    select source_id || ':' || source_item_id as offer_id, * from {{ ref('stg_jobfinder') }}
), n as (select * replace ({{ unesc_num('title') }} as title, {{ unesc_num('company') }} as company, {{ unesc_num('city') }} as city, {{ unesc_num('description') }} as description) from u)
select * replace ({{ unesc_name('title') }} as title, {{ unesc_name('company') }} as company, {{ unesc_name('city') }} as city, trim(regexp_replace({{ unesc_name('description') }}, '\s+', ' ', 'g')) as description) from n
