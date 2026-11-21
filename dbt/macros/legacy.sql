{% macro legacy(table) %}read_parquet('{{ var("legacy") }}/{{ table }}.parquet'){% endmacro %}
