from pathlib import Path
import pandas as pd
import requests
from time import sleep
import duckdb

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DB_PATH = PROJECT_ROOT / "data" / "fred_data.db"
DATA_FILES_PATH = PROJECT_ROOT / "data"

def fetch_fred_data():
    # returns a pandas DF with "CPIAUCSL", "UNRATE", "FEDFUNDS","GDP","PAYEMS" datasets
    API_KEY = "e12d52ceb543405fc7b8a928461fbf5a"
    BASE_URL = "https://api.stlouisfed.org/fred/series/observations"
    METADATA_URL = "https://api.stlouisfed.org/fred/series"

    series_ids = ["CPIAUCSL", "UNRATE", "FEDFUNDS","GDP","PAYEMS"]

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
        sleep(0.2)  # gentle pause

        meta_response = requests.get(METADATA_URL, params=params, timeout=30)
        meta_response.raise_for_status()

        meta_data = meta_response.json()
        meta_data_df = pd.DataFrame(meta_data["seriess"]).copy()
        meta_data_df = meta_data_df.rename(columns={"id": "series_id"})
        all_meta_data_df.append(meta_data_df)
        sleep(0.2)  # gentle pause

    fred_data = pd.concat(all_dfs, ignore_index=True)
    fred_data.name="fred"
    fred_meta_data_df = pd.concat(all_meta_data_df, ignore_index=True)
    fred_meta_data_df.name="fred_metadata"

    return fred_data,fred_meta_data_df

def insert_raw_data():
    con = duckdb.connect(DB_PATH)

    con.execute(f"""
    CREATE OR REPLACE TABLE raw_fred_data AS
    SELECT * FROM read_parquet('{DATA_FILES_PATH}/fred.parquet')
    """)
    con.close()

def insert_raw_metadata():
    con = duckdb.connect(DB_PATH)
    con.execute(f"""
    CREATE OR REPLACE TABLE raw_fred_metadata AS
    SELECT * FROM read_parquet('{DATA_FILES_PATH}/fred_metadata.parquet')
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
    insert_raw_metadata()
    clean_data()