-- 200 extracts for hand annotation, stratified by source and by kept/excluded, reproducible by hash.
select offer_id, source_id, context from {{ ref('salary_text') }}
qualify row_number() over (partition by source_id, excluded is null order by hash(offer_id)) <= 14
order by hash(offer_id) limit 200
