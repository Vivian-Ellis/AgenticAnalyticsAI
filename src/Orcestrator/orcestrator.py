import sys
sys.path.append("../src")
from plan.DataPipeline import DataPlanBuilder,DataLoader
from plan.AnalysisPlanner import AnalysisPlanner
from Analysis import Charts

q=""
data_plan = DataPlanBuilder(q).run()
data_loader = DataLoader(data_plan)
df=data_loader.run()
ap=AnalysisPlanner(data_loader)
results=ap.run()
chart=Charts.Chart(results)
chart.run()

# question="Rank GDP quarters from highest to lowest."

# data_plan = DataPlanBuilder(question).run()

# data_loader = DataLoader(data_plan)
# df=data_loader.run()


# # do for all
# df,dataset_context,DATA_PLANNER=data_planner.build_data_plan(question)

# question_intent=DATA_PLANNER['DATA_PLANNER']

# # if comparision (can do welch, anova, )
# if question_intent=='comparison':
#     comparison.run_comparison_analysis(df,question,DATA_PLANNER,dataset_context)

# # if ranking
# if question_intent=='ranking':
#     ranking.run_ranking_analysis((df,question,DATA_PLANNER,dataset_context))

# # if correlation (can do pearsons and spearmans)
# if question_intent=='correlation':
#     correlation.run_correlation_analysis(df,question,DATA_PLANNER,dataset_context)

# if question_intent=='trend':
#     print('under construction')
#     #     "trend": {
#     #     "default_stat": "mean",
#     #     "default_computation": "aggregated_levels",
#     #     "default_chart": "line"
#     # },

# if question_intent=='volatility':
#     print('under construction')
#     # "volatility": {
#     #     "default_stat": "std",
#     #     "default_computation": "percent_change",
#     #     "default_chart": "bar"
#     # },

# if question_intent=='unsupported':
#     print('under construction')