-- Descriptions that mention an amount and a currency: the only ones salary.py needs to read.
select offre_id as offer_id, source_id, description_nettoyee as description
from {{ legacy('core/offre_source') }}
where offre_id is not null and regexp_matches(description_nettoyee, '(?i)(chf|€|eur|fr\.).{0,40}\d|\d.{0,40}(chf|€|eur)')
