import sys
sys.path.append("../src")
import comparison
import data_planner
import ranking
import correlation
import DataBase.fred_api as fred_api
import analysis
import charts
import DataBase.db as db
import summaries
import user_intent
import date_parser
import time

question="Rank GDP quarters from highest to lowest."

# do for all
df,dataset_context,DATA_PLANNER=data_planner.build_data_plan(question)

question_intent=DATA_PLANNER['DATA_PLANNER']

# if comparision (can do welch, anova, )
if question_intent=='comparison':
    comparison.run_comparison_analysis(df,question,DATA_PLANNER,dataset_context)

# if ranking
if question_intent=='ranking':
    ranking.run_ranking_analysis((df,question,DATA_PLANNER,dataset_context))

# if correlation (can do pearsons and spearmans)
if question_intent=='correlation':
    correlation.run_correlation_analysis(df,question,DATA_PLANNER,dataset_context)

if question_intent=='trend':
    print('under construction')
    #     "trend": {
    #     "default_stat": "mean",
    #     "default_computation": "aggregated_levels",
    #     "default_chart": "line"
    # },

if question_intent=='volatility':
    print('under construction')
    # "volatility": {
    #     "default_stat": "std",
    #     "default_computation": "percent_change",
    #     "default_chart": "bar"
    # },

if question_intent=='unsupported':
    print('under construction')