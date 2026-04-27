import sys
sys.path.append("../src")

import pandas as pd
import analysis
import db
import summaries

def run_case(name, question, context, results_df, stats_df):
    print("\n" + "=" * 80)
    print(name)
    print("=" * 80)

    prompt = summaries.build_prompt(
        question=question,
        context=context,
        results_preview=results_df,
        computed_statistics_preview=stats_df,
    )

    summary = summaries.summarize_prompt(prompt)
    print(summary)
    return summary


df = db.run_query("SELECT * FROM clean_fred_data")

unrate_ts = analysis.get_time_series(df, "UNRATE")
fedfunds_ts = analysis.get_time_series(df, "FEDFUNDS")

context_unrate = summaries.build_context(["UNRATE"])
context_unrate_fed = summaries.build_context(["UNRATE", "FEDFUNDS"])


# Base yearly unemployment table
unrate_yearly = analysis.compute_timeframe_agg(unrate_ts, date_parts=["year"])
unrate_yearly["series_id"] = "UNRATE"

unrate_yearly_pct = analysis.calculate_percent_change(
    unrate_yearly,
    index_field="series_id",
    date_field="year",
    value_field="Average_value",
)


# Case 1: Trend since 2015
results_2015 = analysis.filter_df(unrate_yearly, "year", 2015, ">=")
stats_2015 = analysis.filter_df(unrate_yearly_pct, "year", 2015, ">=")

run_case(
    name="CASE 1 — Unemployment trend since 2015",
    question="How did unemployment change after 2015?",
    context=context_unrate,
    results_df=results_2015,
    stats_df=stats_2015,
)


# Case 2: Trend since 2020
results_2020 = analysis.filter_df(unrate_yearly, "year", 2020, ">=")
stats_2020 = analysis.filter_df(unrate_yearly_pct, "year", 2020, ">=")

run_case(
    name="CASE 2 — Average unemployment since 2020",
    question="How has the average unemployment rate changed since 2020?",
    context=context_unrate,
    results_df=results_2020,
    stats_df=stats_2020,
)


# Case 3: Monthly comparison 2024 vs 2025
unrate_monthly = analysis.compute_timeframe_agg(unrate_ts, date_parts=["year", "month"])
monthly_2024_2025 = analysis.filter_df(unrate_monthly, "year", [2024, 2025], "in")

run_case(
    name="CASE 3 — Monthly unemployment comparison: 2024 vs 2025",
    question="Compare monthly average unemployment rates in 2024 versus 2025.",
    context=context_unrate,
    results_df=monthly_2024_2025,
    stats_df=monthly_2024_2025,
)


# Case 4: Lowest unemployment years since 2010
unrate_since_2010 = filter_df(unrate_yearly, "year", 2010, ">=")
lowest_years = analysis.rank_periods(
    unrate_since_2010,
    sort_by="Average_value",
    n=10,
    ascending=True,
)

run_case(
    name="CASE 4 — Lowest unemployment years since 2010",
    question="Rank the lowest unemployment years since 2010.",
    context=context_unrate,
    results_df=lowest_years,
    stats_df=unrate_since_2010,
)


# Case 5: Highest unemployment years since 2010
highest_years = analysis.rank_periods(
    unrate_since_2010,
    sort_by="Average_value",
    n=10,
    ascending=False,
)

run_case(
    name="CASE 5 — Highest unemployment years since 2010",
    question="Rank the highest unemployment years since 2010.",
    context=context_unrate,
    results_df=highest_years,
    stats_df=unrate_since_2010,
)


# Case 6: Volatility since 2010
most_volatile_years = analysis.rank_periods(
    unrate_since_2010,
    sort_by="std_value",
    n=10,
    ascending=False,
)

run_case(
    name="CASE 6 — Most volatile unemployment years since 2010",
    question="Which years had the most unemployment volatility since 2010?",
    context=context_unrate,
    results_df=most_volatile_years,
    stats_df=unrate_since_2010,
)


# Case 7: UNRATE vs FEDFUNDS since 2020
combined = analysis.get_time_series(df, ["UNRATE", "FEDFUNDS"])
combined_since_2020 = filter_df(combined, "year", 2020, ">=")

combined_yearly = analysis.compute_timeframe_agg(
    combined_since_2020,
    date_parts=["year", "series_id"],
)

comparison_wide = analysis.compare_series(
    combined_yearly,
    index_field="year",
    columns_field="series_id",
    value_field="Average_value",
)

correlation = analysis.calculate_correlation(comparison_wide)

run_case(
    name="CASE 7 — Compare unemployment and federal funds rate since 2020",
    question="Compare average unemployment and the federal funds rate since 2020.",
    context=context_unrate_fed,
    results_df=comparison_wide,
    stats_df=correlation,
)