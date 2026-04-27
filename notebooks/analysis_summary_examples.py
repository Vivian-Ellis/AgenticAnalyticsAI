import sys
sys.path.append("../src")

import analysis
import db
import summaries

df=db.run_query("SELECT * FROM clean_fred_data")

UNRATE_metadata=db.get_series_metadata(series_id="UNRATE")

unrate_ts = analysis.get_time_series(df,"UNRATE")

# Question asks about levels/averages → pass compute_timeframe_agg()
unrate_yearly_agg=analysis.compute_timeframe_agg(unrate_ts,date_parts=["year"])

# Question asks about change rate/volatility → pass calculate_percent_change()
unrate_yearly_agg['series_id']='UNRATE'
unrate_yearly_pct_change = analysis.calculate_percent_change(unrate_yearly_agg,index_field="series_id",date_field="year",value_field="Average_value")

# Question asks about comparison → pass aggregated comparison table
unrate_payems_wide_df=analysis.compare_series(df[df['series_id'].isin(["PAYEMS","UNRATE"])])


context=summaries.build_context(["UNRATE"])

#------------------QUESTIONS-----------------
# Question asks about change rate/volatility → pass calculate_percent_change()

# q1
#datasets to be summarized
results_preview2015 = summaries.build_stats_preview(unrate_yearly_agg,11)
computed_statistics_preview2015 = summaries.build_stats_preview(unrate_yearly_pct_change,11)

#claude analytical summary
prompt1=summaries.build_prompt("How did unemployment change after 2015?", context, results_preview2015, computed_statistics_preview2015)
summary = summaries.summarize_prompt(prompt1)

print(summary)

# q2
# yearly aggregation narration
results_preview2020 = summaries.build_stats_preview(unrate_yearly_agg,6)
computed_statistics_preview2020 = summaries.build_stats_preview(unrate_yearly_pct_change,6)

#claude analytical summary
prompt2=summaries.build_prompt("how has the average unemployment rate changed since 2020?", context, results_preview2020, computed_statistics_preview2020)
summary = summaries.summarize_prompt(prompt2)

print(summary)

# q3
# comparison narration
unrate_monthly_agg=analysis.compute_timeframe_agg(unrate_ts,date_parts=["date"])
results_preview2024 = summaries.build_results_preview(unrate_monthly_agg,"date","2024-01-01",">=")

#claude analytical summary
prompt3=summaries.build_prompt("how has the average unemployment rate changed since 2020?", context, results_preview2024, results_preview2024)
summary = summaries.summarize_prompt(prompt3)

print(summary)

# q4
# ranking narration
unrateyearly2010=analysis.compute_timeframe_agg(unrate_ts,date_parts=["year"])
unrateyearly2010 = summaries.build_results_preview(unrateyearly2010,"year",2010,">=")

unrateyearly2010=analysis.rank_periods(unrateyearly2010, sort_by=["Average_value"], n=16, ascending=True)

#claude analytical summary
prompt4=summaries.build_prompt("rank the lowest unemployment years since 2010", context, unrateyearly2010, unrateyearly2010)
summary = summaries.summarize_prompt(prompt4)

print(summary)