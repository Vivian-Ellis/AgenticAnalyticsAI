# TO-DO: build out
# import sys
# sys.path.append("../src/")

# import Analysis.analysis as analysis
# import Narration.summaries as summaries
# import DataBase.semantics as semantics
# from Analysis.AnalysisResults import TrendResult

# class RankingAnalysis:
#     def __init__(self,data_loader):
#         self.summary_narration=None
#         self.original_df=None
#         self.ranked_df=None
#         self.ascending_bool=None
#         self.n=None
#         self.series_semantics=None
#         self.data_loader=data_loader

#     def run_analysis(self):
#         df=self.data_loader.data.copy()

#         # STEP 1 
        

#         #STEP ? send results to claude & return string
#         self.summary_narration=summaries.run_trend_analysis(self.data_loader.data_plan.question,
#                                                 self.data_loader.data_plan.dataset_context,
#                                                 df,
#                                                 self.ranked_df,
#                                                 sort_field="Value",
#                                                 ascending=self.ascending_bool,
#                                                 n=self.n,
#                                                 aggregation_method="mean",
#                                                 group_by=self.data_loader.data_plan.date_grain)
        
#         return TrendResult(
#                     question=self.data_loader.data_plan.question,
#                     intent=self.data_loader.data_plan.question_intent,
#                     series_ids=self.data_loader.data_plan.series_ids,
#                     date_grain=self.data_loader.data_plan.date_grain,
#                     summary_narration=self.summary_narration,
#                     ranked_df=self.ranked_df,
#                     original_df=self.original_df,
#                     ascending=self.ascending_bool,
#                     n=self.n,
#                     series_semantics=self.series_semantics)