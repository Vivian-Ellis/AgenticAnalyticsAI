import duckdb
import src.charts as charts
import pandas as pd

con = duckdb.connect("raw_data.db")

df=(con.execute("""
SELECT *
FROM clean_fred_data
""").fetchdf())

print(
con.execute("""
SELECT count(*),date,series_id
FROM clean_fred_data
group by 2,3
""").fetchdf()
)


df2=df.groupby(["date","series_id"]).agg(Total_value=('value', 'sum'),
                                        Average_value=('value', 'mean')).reset_index()

charts.plot_bar(df2, "series_id", "Total_value","Bar Chart Sample Total")
charts.plot_bar(df2, "series_id", "Average_value","Bar Chart Sample Average")
charts.plot_time_series(df2[df2["series_id"]=="UNRATE"], "date", "Total_value","Time Series Sample") 


