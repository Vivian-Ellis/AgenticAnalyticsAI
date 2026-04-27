import duckdb
import pandas as pd
con = duckdb.connect("raw_data.db")

con.execute("""
CREATE OR REPLACE TABLE raw_fred_data AS
SELECT * FROM read_parquet('fred_data.parquet')
""")

print(con.execute("SELECT * FROM raw_fred_data LIMIT 5").fetchdf())

# Clean layer
con.execute("""
CREATE OR REPLACE TABLE clean_fred_data AS
SELECT
    date,
    value,
    series_id
FROM raw_fred_data
WHERE value IS NOT NULL
""")