{# Latest version of each item of a source, with its first and last sighting; raw days plus compacted months. #}
{% macro raw(source) %}
{% set root = "r2://" ~ env_var("R2_BUCKET", "jobradar-data") %}
{% set compacted = run_query("select count(*) from glob('" ~ root ~ "/compact/*/data.parquet')").columns[0][0] > 0 if execute else false %}
{% set stored = run_query("select count(*) from glob('" ~ root ~ "/raw/source=" ~ source ~ "/*/*.parquet')").columns[0][0] > 0 if execute else false %}
(select item_id, body, min(first_seen) over w as first_seen, max(last_seen) over w as last_seen
from (
    select null::varchar as item_id, null::varchar as body, null::timestamptz as first_seen, null::timestamptz as last_seen where false
    {% if stored %}
    union all
    select item_id, body, fetched_at as first_seen, fetched_at as last_seen
    from read_parquet('{{ root }}/raw/source={{ source }}/*/*.parquet')
    {% endif %}
    {% if compacted %}
    union all
    select item_id, body, first_seen, last_seen from read_parquet('{{ root }}/compact/*/data.parquet') where source = '{{ source }}'
    {% endif %}
)
window w as (partition by item_id)
qualify row_number() over (partition by item_id order by last_seen desc) = 1)
{% endmacro %}
