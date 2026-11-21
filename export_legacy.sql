INSTALL sqlite; LOAD sqlite; SET sqlite_all_varchar = true;
CREATE SECRET (TYPE r2, KEY_ID getenv('R2_KEY_ID'), SECRET getenv('R2_SECRET'), ACCOUNT_ID getenv('R2_ACCOUNT_ID'));
SET VARIABLE src = getenv('LEGACY');
ATTACH getvariable('src') AS legacy (READ_ONLY);
CREATE TEMP TABLE parts AS SELECT schema_name s, table_name t, format('{}/{}.{}.parquet', getenv('DEST'), schema_name, table_name) f
FROM duckdb_tables() WHERE database_name = 'legacy';
.mode list
.headers off
.output copy_legacy.sql
SELECT format('COPY legacy."{}"."{}" TO ''{}'' (COMPRESSION zstd);', s, t, f) FROM parts;
SELECT format('INSERT INTO counts SELECT ''{0}.{1}'', (SELECT count(*) FROM legacy."{0}"."{1}"), (SELECT count(*) FROM ''{2}'');', s, t, f) FROM parts;
.output
CREATE TEMP TABLE counts (tbl VARCHAR, vps BIGINT, r2 BIGINT);
.read copy_legacy.sql
.mode table
.headers on
SELECT *, vps = r2 AS ok FROM counts ORDER BY tbl;
SELECT CASE WHEN count(*) = 0 OR bool_or(vps <> r2) THEN error('row counts differ') END AS failed FROM counts;
