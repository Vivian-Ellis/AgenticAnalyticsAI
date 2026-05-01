import pandas as pd
import numpy as np
import scipy.stats as stats
from scipy import stats
from statsmodels.stats.multicomp import pairwise_tukeyhsd

def get_time_series(df, series_ids=None):
    """
    Returns a dataframe with extracted date parts and sorted by date.

    series_ids is optional; by default selects all available series.
    Accepts either a string or a list of strings.
    """
    if series_ids is None:
        series_ids = ["CPIAUCSL", "UNRATE", "FEDFUNDS","GDP","PAYEMS"]
    elif isinstance(series_ids, str):
        series_ids = [series_ids]

    timeseries_df= df[df['series_id'].isin(series_ids)][["date","value","series_id"]].copy()
    timeseries_df["day"]=timeseries_df["date"].dt.day
    timeseries_df["month"]=timeseries_df["date"].dt.month
    timeseries_df["quarter"]=timeseries_df["date"].dt.quarter
    timeseries_df["year"]=timeseries_df["date"].dt.year
    timeseries_df=timeseries_df.sort_values("date",ascending=False)
    return timeseries_df

def compute_timeframe_agg(timeseries_df,date_parts="date"):
    """
    Compute average value grouped by the provided date parts.
    Expects timeseries_df to already be filtered to the intended series.

    date_parts may be a string or list, such as:
    "date", ["year"], or ["year", "quarter"].
    """
    timeseries_df_agg=timeseries_df.groupby(date_parts).agg(Average_value=("value","mean"),
                                                 Min_value=("value","min"),
                                                 Max_value=("value","max"),
                                                 Median_value=("value","median"),
                                                 std_value=("value","std"),
                                                 var_value=("value","var"),
                                                 row_count=(date_parts,"count")
                                                 ).reset_index()

    timeseries_df_agg=timeseries_df_agg.sort_values(by=date_parts,ascending=False)
    return timeseries_df_agg

def compare_series(df,index_field="date",columns_field="series_id",value_field="value"):
    """
    Returns a wide dataframe for comparing multiple series by date.
    This function performs no calculations. Missing values remain NaN
    when one series has no observation for a given date IE full outer join
    """
    # df2=get_time_series(df,series_ids)
    return df.pivot(index=index_field, columns=columns_field, values=value_field).reset_index().sort_values(index_field)

def calculate_percent_change(df,index_field="series_id",date_field="date",value_field="value"):
    """
    Compute the percentage change value
    """
    compare_df=compare_series(df,date_field,index_field,value_field)
    compare_df=compare_df.set_index(date_field)
    pct_change_df=compare_df.pct_change()*100
    pct_change_df= pct_change_df.reset_index()
    return pct_change_df.sort_values(date_field,ascending=False)

def rank_periods(df, sort_by, n=10, ascending=False):
    """
    Rank rows by one or more columns.

    sort_by can be a string or list of strings.
    """
    if n >=1:
        return df.sort_values(by=sort_by, ascending=ascending).head(abs(n))
    else:
        return df.sort_values(by=sort_by, ascending=ascending)

def filter_df(df, field, value, operator=">="):
    if operator == ">=":
        return df[df[field] >= value].copy()
    if operator == ">":
        return df[df[field] > value].copy()
    if operator == "<=":
        return df[df[field] <= value].copy()
    if operator == "<":
        return df[df[field] < value].copy()
    if operator == "==":
        return df[df[field] == value].copy()
    if operator == "in":
        return df[df[field].isin(value)].copy()
    raise ValueError(f"Unsupported operator: {operator}")

def df_time_filter(df,start_date,end_date):
    return df[(df["date"] >= start_date)&(df["date"]<=end_date)].copy()

def compute_df_aggregation(df,group_by_fields="date",computation="mean"):
    """
    Expects df to already be filtered to the intended series.

    group_by_fields may be a string or list, such as:
    "date", ["year"], or ["year", "quarter"]
    """
    df_agg=df.groupby(group_by_fields).agg(calculated_value=("value",computation)).reset_index()
    return df_agg

def parse_date(df):
    """
    Returns a dataframe with extracted date parts.
    Expects df to already be filtered to the intended series and have a field called "date"
    """
    df["day"]=df["date"].dt.day
    df["month"]=df["date"].dt.month
    df["quarter"]=df["date"].dt.quarter
    df["year"]=df["date"].dt.year
    return df