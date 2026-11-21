-- Offers collected since phase 3, one row per posting across sources.
select source_id || ':' || source_item_id as offer_id, * from {{ ref('stg_job_room') }}
union all by name
select source_id || ':' || source_item_id, * from {{ ref('stg_eures') }}
union all by name
select source_id || ':' || source_item_id, * from {{ ref('stg_adem') }}
