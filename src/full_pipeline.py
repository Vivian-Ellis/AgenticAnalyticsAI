import comparison
import data_planner

import sys
sys.path.append("../src")

import fred_api
import analysis
import charts
import db
import summaries
import user_intent
import date_parser
import time

# do for all
df,dataset_context,DATA_PLANNER=data_planner.build_data_plan("Rank GDP quarters from highest to lowest.")

# if comparision
comparison.run_comparison_analysis(df,user_question,DATA_PLANNER,dataset_context)

# if ranking
