from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.append(str(SRC_DIR))

import Analysis.analysis as analysis
import Narration.summaries as summaries
from scipy.stats import shapiro
import numpy as np
from Analysis.AnalysisResults import CorrelationResult

class CorrelationAnalysis:
    def __init__(self,data_loader):
        self.data_loader=data_loader
        self.spearman_reason=[]
        self.corr_method='pearson'
        self.corr_df=None
        self.summary_narration=None
        self.original_df=None

    def shapiro_normality_test(self,data):
        # The Shapiro-Wilk will be used to test for normailty where:
        # H_0 : the sample is drawn from a normally distributed population
        # H_1 : the sample is drawn from a population that is not normally distributed
        # Let the threshold for significance be 0.01 so that if p_value < 0.01, I rejected the null hypothesis and conclude that the data is not normally distributed.
        stat, p = shapiro(data)

        # let the significance level be 0.01
        alpha = 0.01

        if p > alpha: #fail to reject null hypothesis, normal
            return True
        else: #reject null hypothesis, not normal.
            return False

    def find_outliers(self,data):
        Q1 = data.quantile(0.25)
        Q3 = data.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        outliers = data[(data < lower_bound) | (data > upper_bound)]
        return len(outliers)

    def calculate_correlation(self,compare_df):
        numeric_df = compare_df.select_dtypes(include=[np.number])

        for series in self.data_loader.data_plan.series_ids:

            # if any outliers switch to spearman
            if self.find_outliers(compare_df[series]) > 0:
                self.corr_method="spearman"
                self.spearman_reason.append(f"{series} contained detected outliers.")

            # if non-noraml switch to spearman
            if self.shapiro_normality_test(compare_df[series]) == False:
                self.corr_method="spearman"
                self.spearman_reason.append(f"{series} violated the configured normality threshold.")

        corr_df=numeric_df.corr(method=self.corr_method)
        corr_df.index.name = None

        self.corr_df=corr_df

        return corr_df

    def run_analysis(self):
        df=self.data_loader.data.copy()

        # STEP 1 get the aggregate df
        self.stats_df=analysis.compute_df_aggregation(
            df,
            group_by_fields=["series_id",self.data_loader.data_plan.date_grain],
            computation="mean"
        )

        # STEP 2 create the wide df
        self.original_df=analysis.compare_series(
            df,
            index_field="date",
            columns_field="series_id",
            value_field="value"
        )

        # STEP 3 compute appropriate correlation
        self.corr_df=self.calculate_correlation(self.original_df)

        #STEP 4 send results to claude & return string
        if self.corr_method=='pearson':
            self.summary_narration=summaries.run_pearson_correlation_analysis(
                self.data_loader.data_plan.question,
                self.data_loader.data_plan.dataset_context,
                self.corr_df,
                self.original_df
            )

        if self.corr_method=='spearman':
            spearman_reason="\n".join(self.spearman_reason)

            self.summary_narration=summaries.run_spearman_correlation_analysis(
                self.data_loader.data_plan.question,
                self.data_loader.data_plan.dataset_context,
                self.corr_df,
                self.stats_df,
                spearman_reason
            )

        return CorrelationResult(
                    question=self.data_loader.data_plan.question,
                    intent=self.data_loader.data_plan.question_intent,
                    series_ids=self.data_loader.data_plan.series_ids,
                    date_grain=self.data_loader.data_plan.date_grain,
                    summary_narration=self.summary_narration,
                    corr_df=self.corr_df,
                    original_df=self.original_df,
                    corr_method=self.corr_method,
                    spearman_reason=self.spearman_reason)