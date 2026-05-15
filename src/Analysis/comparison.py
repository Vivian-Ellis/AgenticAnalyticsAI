import sys
sys.path.append("../src/")
import Narration.summaries as summaries
import pandas as pd
import scipy.stats as stats
from scipy import stats
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from Analysis.AnalysisResults import ComparisonResult

class ComparisonAnalysis:
    def __init__(self,data_loader,alpha=0.05):
        self.summary_narration=None
        self.descriptive_statistics=None
        self.stats_test_results=None
        self.data_loader=data_loader
        self.alpha=alpha
        self.comparison_stats_plan = {
            "average_comparison": {
                "description": "Compare group averages, means, levels, or rates.",
                "example_triggers": ["average", "mean", "level", "rate"],
                "tests": {
                    "2_groups": "welch_ttest",
                    "3plus_groups": "anova"
                },
                "calculation": "mean"
            },

            "median_comparison": {
                "description": "Compare group medians or compare groups when distributions are skewed or non-normal.",
                "example_triggers": ["median", "skewed", "non-normal", "outliers"],
                "tests": {
                    "2_groups": "mann_whitney_u",
                    "3plus_groups": "kruskal_wallis"
                },
                "calculation": "median"
            },

            "relationship_comparison": {
                "description": "Compare relationships, associations, co-movement, or trends between variables over time.",
                "example_triggers": ["relationship", "association", "trend", "movement", "over time", "since"],
                "tests": {
                    "default": "correlation",
                    "prediction_modeling": "linear_regression"
                },
                "calculation": "corr"
            },

            "volatility_comparison": {
                "description": "Compare variability, volatility, fluctuations, stability, dispersion, or consistency.",
                "example_triggers": ["volatility", "variability", "fluctuation", "stability"],
                "tests": {
                    "default": "variance"
                },
                "calculation": "var"
            },

            "distribution_comparison": {
                "description": "Compare full distributions, distribution shape, spread, skewness, or percentile behavior.",
                "example_triggers": ["distribution", "spread", "skewness", "percentile"],
                "tests": {
                    "default": "ks_test"
                },
                "calculation": "quantile"
            },

            "before_after_comparison": {
                "description": "Compare values before and after an event, cutoff, or time period.",
                "example_triggers": ["before", "after", "pre/post", "prior to"],
                "tests": {
                    "default": "welch_ttest"
                },
                "calculation": "mean"
            },

            "ranked_extremes_comparison": {
                "description": "Compare highest vs lowest, top vs bottom, or ranked extreme groups.",
                "example_triggers": ["highest", "lowest", "top", "bottom", "best", "worst"],
                "tests": {
                    "2_groups": "welch_ttest",
                    "3plus_groups": "anova"
                },
                "calculation": "mean"
            }
        }

        self.comparison_routing_priority = [
            "before_after_comparison",
            "ranked_extremes_comparison",
            "volatility_comparison",
            "distribution_comparison",
            "relationship_comparison",
            "median_comparison",
            "average_comparison"
        ]

        self.statistical_test_registry = {
            "welch_ttest": self.welch_ttest,
            "anova": self.one_way_anova
            # "mann_whitney_u": self.mann_whitney_u,
            # "kruskal_wallis": self.kruskal_wallis,
            # "correlation": self.correlation,
            # "linear_regression": self.linear_regression,
            # "variance": self.variance_comparison,
            # "ks_test": self.ks_test
        }

    def run_analysis(self):
        df=self.data_loader.data.copy()
        num_groups=df[self.data_loader.data_plan.date_grain].nunique()
        # STEP 1 derive plan
        results=summaries.comparison_method_intent(self.data_loader.data_plan.question,
                                                     self.data_loader.data_plan.date_grain,
                                                     num_groups,
                                                     self.comparison_routing_priority,
                                                     self.comparison_stats_plan)
        
        comparison_type, statistical_test = results.split(",")
        comparison_type = comparison_type.strip()
        statistical_test = statistical_test.strip()

        #STEP 2 conduct appropriate test
        stats_test_function = self.statistical_test_registry[statistical_test]
        self.descriptive_statistics, self.stats_test_results = stats_test_function(df)
  
        #STEP 3 send results to claude & return string
        self.summary_narration= summaries.run_comparison_analysis(self.data_loader.data_plan.question,
                                                 self.data_loader.data_plan.dataset_context,
                                                 comparison_type,
                                                 statistical_test,
                                                 df,
                                                 self.descriptive_statistics,
                                                 self.stats_test_results)
        
        return ComparisonResult(
            question=self.data_loader.data_plan.question,
            intent=self.data_loader.data_plan.question_intent,
            series_ids=self.data_loader.data_plan.series_ids,
            date_grain=self.data_loader.data_plan.date_grain,
            original_df=df,
            summary_narration=self.summary_narration,
            descriptive_statistics=self.descriptive_statistics,
            comparison_type=comparison_type,
            statistical_test=statistical_test,
            inferential_statistics=self.stats_test_results,
            alpha=self.alpha
        )


    def welch_ttest(self,df):
        descriptive_statistics=df.groupby(self.data_loader.data_plan.date_grain).agg(Value=("value","mean")).reset_index()
        groups=[]
        for g in df[self.data_loader.data_plan.date_grain].unique():
            groups.append(df[df[self.data_loader.data_plan.date_grain]==g]["value"])
        # Conduct Welch's t-Test and return/save the result
        welch_ttest_results=stats.ttest_ind(groups[0], groups[1], equal_var = False)
        return descriptive_statistics,welch_ttest_results

    def one_way_anova(self,df):
        anova_results = {
            "f_stat": None,
            "p_value": None,
            "alpha": self.alpha,
            "tukey": None
        }

        descriptive_statistics = (
            df.groupby(self.data_loader.data_plan.date_grain)
            .agg(Value=("value", "mean"))
            .reset_index()
        )
        groups=[]
        for g in df[self.data_loader.data_plan.date_grain].unique(): 
            groups.append(df[df[self.data_loader.data_plan.date_grain]==g]["value"]) 
        
        f_stat, p_value = stats.f_oneway(*groups)

        anova_results["f_stat"] = f_stat
        anova_results["p_value"] = p_value

        if p_value <= self.alpha:
            tukey = pairwise_tukeyhsd(
                endog=df["value"],
                groups=df[self.data_loader.data_plan.date_grain],
                alpha=self.alpha
            )
            tukey_df = pd.DataFrame(
                data=tukey._results_table.data[1:],
                columns=tukey._results_table.data[0]
            )
            anova_results["tukey"] = tukey_df
        return descriptive_statistics, anova_results