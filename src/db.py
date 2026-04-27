import duckdb

DB_PATH = "../data/fred_data.db"

def get_connection():
    """
    Create and return a DuckDB connection.
    """
    return duckdb.connect(DB_PATH)

def run_query(query):
    """
    Run a SQL query and return the results as a pandas DataFrame.
    """
    con = get_connection()
    df = con.execute(query).fetchdf()
    con.close()
    return df

def list_tables():
    """
    Return all tables in the DuckDB database.
    """
    query = """
    SHOW TABLES
    """
    return run_query(query)

def get_available_series(table_name="clean_fred_data"):
    """
    Return the distinct series IDs available in the given table.
    """
    query = f"""
    SELECT DISTINCT series_id
    FROM {table_name}
    ORDER BY series_id
    """
    return run_query(query)

def describe_table(table_name):
    """
    Return schema information for a given table.
    """
    query = f"""
    DESCRIBE {table_name}
    """
    return run_query(query)

def get_series_metadata(series_id=None):
    if series_id:
        query = f"""
        SELECT
            series_id,
            title,
            frequency,
            units,
            seasonal_adjustment,
            observation_start,
            observation_end,
            notes
        FROM raw_fred_metadata
        WHERE series_id='{series_id}'
        ORDER BY series_id
        """
        return run_query(query)
    else:
        query = """
        SELECT
            series_id,
            title,
            frequency,
            units,
            seasonal_adjustment,
            observation_start,
            observation_end,
            notes
        FROM raw_fred_metadata
        ORDER BY series_id
        """
        return run_query(query)

def get_date_ranges(table_name="clean_fred_data"):
    """
    Return the minimum and maximum date for each series_id.
    """
    query = f"""
    SELECT
        series_id,
        MIN(date) AS min_date,
        MAX(date) AS max_date,
        COUNT(*) AS row_count
    FROM {table_name}
    GROUP BY series_id
    ORDER BY series_id
    """
    return run_query(query)

def get_table_preview(table_name="clean_fred_data", limit=5):
    """
    Return the first few rows of a table.
    """
    query = f"""
    SELECT *
    FROM {table_name}
    LIMIT {limit}
    """
    return run_query(query)