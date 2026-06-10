from pathlib import Path
import pandas as pd
import requests
from time import sleep
import duckdb
import os

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DB_PATH = PROJECT_ROOT / "data" / "fred_data.db"
DATA_FILES_PATH = PROJECT_ROOT / "data"

API_KEY = os.getenv("FRED_API_KEY")

def fetch_fred_data():
    # returns a pandas DF with "CPIAUCSL", "UNRATE", "FEDFUNDS","GDP","PAYEMS" datasets

    BASE_URL = "https://api.stlouisfed.org/fred/series/observations"
    METADATA_URL = "https://api.stlouisfed.org/fred/series"

    # series_ids = ["CPIAUCSL", "UNRATE", "FEDFUNDS","GDP","PAYEMS"] #og series
    series_ids = [
        "CPIAUCSL",  # Inflation
        "UNRATE",    # Unemployment
        "PAYEMS",    # Jobs
        "GDP",       # GDP
        "FEDFUNDS",  # Interest Rates
        "DGS10",     # Treasury Yield
        "M2SL",      # Money Supply
        "SP500"      # Stock Market
        ]#expanded series
    
    all_dfs = []
    all_meta_data_df=[]

    for series_id in series_ids:
        params = {
            "series_id": series_id,
            "api_key": API_KEY,
            "file_type": "json",
        }
        
        response = requests.get(BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        # normalize the datatypes and coerce any errors on value
        df = pd.DataFrame(data["observations"])[["date", "value"]].copy()
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df["series_id"] = series_id    
        all_dfs.append(df)
        sleep(1)  # gentle pause

        meta_response = requests.get(METADATA_URL, params=params, timeout=30)
        meta_response.raise_for_status()

        meta_data = meta_response.json()
        meta_data_df = pd.DataFrame(meta_data["seriess"]).copy()
        meta_data_df = meta_data_df.rename(columns={"id": "series_id"})
        all_meta_data_df.append(meta_data_df)
        sleep(1)  # gentle pause

    fred_data = pd.concat(all_dfs, ignore_index=True)
    fred_data.name="fred_data"
    fred_meta_data_df = pd.concat(all_meta_data_df, ignore_index=True)
    fred_meta_data_df.name="fred_meta_data"

    return fred_data,fred_meta_data_df

def insert_raw_data():
    con = duckdb.connect(DB_PATH)

    con.execute(f"""
    CREATE OR REPLACE TABLE raw_fred_data AS
    SELECT * FROM read_parquet('{DATA_FILES_PATH}/fred_data.parquet')
    """)
    con.close()

def insert_raw_metadata():
    con = duckdb.connect(DB_PATH)
    con.execute(f"""
    CREATE OR REPLACE TABLE raw_fred_metadata AS
    SELECT * FROM read_parquet('{DATA_FILES_PATH}/fred_meta_data.parquet')
    """)
    con.close()

def clean_metadata():
    con = duckdb.connect(DB_PATH)
    # Clean layer
    con.execute("""
    CREATE OR REPLACE TABLE clean_fred_metadata AS
    SELECT series_id,
        split(title, ':')[1] as title,
        frequency,
        units,
        seasonal_adjustment,
        observation_start,
        observation_end,
        notes,
        CASE series_id
            WHEN 'CPIAUCSL' THEN 'Consumer Price Index (CPI)'
            WHEN 'UNRATE' THEN 'Unemployment Rate'
            WHEN 'PAYEMS' THEN 'Total Nonfarm Payroll Employment'
            WHEN 'GDP' THEN 'Gross Domestic Product (GDP)'
            WHEN 'FEDFUNDS' THEN 'Federal Funds Effective Rate'
            WHEN 'DGS10' THEN '10-Year Treasury Yield'
            WHEN 'M2SL' THEN 'M2 Money Supply'
            WHEN 'SP500' THEN 'S&P 500 Index'
    END AS updated_title,
        CASE series_id
            WHEN 'CPIAUCSL' THEN 'Measures the average price level of goods and services purchased by urban consumers. Commonly used as the primary measure of inflation.'
            WHEN 'UNRATE' THEN 'Measures the percentage of the labor force that is unemployed and actively seeking work.'
            WHEN 'PAYEMS' THEN 'Measures total U.S. nonfarm payroll employment and is commonly used to track job growth and labor market strength.'
            WHEN 'GDP' THEN 'Measures the total market value of goods and services produced within the United States and serves as a primary indicator of economic output.'
            WHEN 'FEDFUNDS' THEN 'Measures the overnight interest rate banks charge each other for reserve lending and is the Federal Reserve''s primary policy rate.'
            WHEN 'DGS10' THEN 'Measures the yield on 10-year U.S. Treasury securities and serves as a benchmark for long-term interest rates.'
            WHEN 'M2SL' THEN 'Measures the U.S. money supply, including cash, checking deposits, savings deposits, and other liquid assets.'
            WHEN 'SP500' THEN 'Measures the performance of 500 large U.S. publicly traded companies and is a widely used indicator of the stock market.'
        END AS description
    FROM raw_fred_metadata
    """)
    con.close()

def save_csv_parquet(df):
    csv_path = DATA_FILES_PATH/f"{df.name}.csv"
    parquet_path = DATA_FILES_PATH/f"{df.name}.parquet"
    df.to_csv(csv_path, index=False)
    df.to_parquet(parquet_path, index=False)
    print(f"Saved {csv_path}")
    print(f"Saved {parquet_path}")

def clean_data():
    con = duckdb.connect(DB_PATH)
    # Clean layer
    con.execute("""
    CREATE OR REPLACE TABLE clean_fred_data AS
    SELECT
        date,
        value,
        series_id
    FROM raw_fred_data
    WHERE value IS NOT NULL AND date IS NOT NULL
    """)
    con.close()

def build_fred_dataset():
    fred_data,fred_meta_data_df=fetch_fred_data()
    fred_data.name="fred_data"
    fred_meta_data_df.name="fred_meta_data"
    save_csv_parquet(fred_data)
    save_csv_parquet(fred_meta_data_df)
    insert_raw_data()
    clean_data()

    insert_raw_metadata()
    clean_metadata()