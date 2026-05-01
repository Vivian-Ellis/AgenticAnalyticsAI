import sys
sys.path.append("../src")

import analysis
import summaries
import semantics

def run_ranking_analysis(df,question,DATA_PLANNER,dataset_context):
    # STEP 1 understand dataset semantics
    series_semantics=semantics.dataset_ranking_semantics(DATA_PLANNER['series_ids'])
    prompt=summaries.build_ranking_method_prompt("Rank GDP quarters from highest to lowest.",series_semantics)
    result=summaries.run_prompt(prompt)

    #STEP 2 get the ranking order
    ascending_bool=result.split(",")[0] == "True"
    n=int(result.split(",")[1])

    #STEP 3 compute ranking and aggregation
    df_agg=analysis.compute_df_aggregation(df,group_by_fields=DATA_PLANNER['date_grain'],computation="mean")
    ranked_df=analysis.rank_periods(df_agg, sort_by="calculated_value", n=n, ascending=ascending_bool)

    #STEP 4 send results to claude & return string
    return summaries.run_ranking_analysis(question,dataset_context,df,ranked_df)