from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.append(str(SRC_DIR))

import Analysis.analysis as analysis
import Narration.summaries as summaries
import DataBase.semantics as semantics
from Analysis.AnalysisResults import RankingResult

class RankingAnalysis:
    def __init__(self,data_loader):
        self.summary_narration=None
        self.original_df=None
        self.ranked_df=None
        self.ascending_bool=None
        self.n=None
        self.series_semantics=None
        self.data_loader=data_loader

    def run_analysis(self):
        df=self.data_loader.data.copy()

        # STEP 1 understand dataset semantics
        self.series_semantics=semantics.dataset_ranking_semantics(self.data_loader.data_plan.series_ids)
        prompt=summaries.build_ranking_method_prompt(self.data_loader.data_plan.question,self.series_semantics)
        result=summaries.run_prompt(prompt)

        #STEP 2 get the ranking order
        self.ascending_bool=result.split(",")[0] == "True"
        self.n=int(result.split(",")[1])

        #STEP 3 compute ranking and aggregation
        self.original_df=analysis.compute_df_aggregation(df,group_by_fields=self.data_loader.data_plan.date_grain,computation="mean")
        self.ranked_df=analysis.rank_periods(self.original_df, sort_by="Value", n=self.n, ascending=self.ascending_bool)

        #STEP 4 send results to claude & return string
        self.summary_narration=summaries.run_ranking_analysis(self.data_loader.data_plan.question,
                                                self.data_loader.data_plan.dataset_context,
                                                df,
                                                self.ranked_df,
                                                sort_field="Value",
                                                ascending=self.ascending_bool,
                                                n=self.n,
                                                aggregation_method="mean",
                                                group_by=self.data_loader.data_plan.date_grain)
        
        return RankingResult(
                    question=self.data_loader.data_plan.question,
                    intent=self.data_loader.data_plan.question_intent,
                    series_ids=self.data_loader.data_plan.series_ids,
                    date_grain=self.data_loader.data_plan.date_grain,
                    summary_narration=self.summary_narration,
                    ranked_df=self.ranked_df,
                    original_df=self.original_df,
                    ascending=self.ascending_bool,
                    n=self.n,
                    series_semantics=self.series_semantics)