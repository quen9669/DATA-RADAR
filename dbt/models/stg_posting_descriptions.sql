-- Same filter as stg_descriptions, on the postings collected since phase 3.
select offer_id, source_id, description from {{ ref('postings') }}
where regexp_matches(description, '(?i)(chf|€|eur|fr\.).{0,40}\d|\d.{0,40}(chf|€|eur)')
