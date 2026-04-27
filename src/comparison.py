import sys
sys.path.append("../src")

import analysis
import summaries
import user_intent

COMPARISON_STATS_PLAN = {
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
COMPARISON_ROUTING_PRIORITY = [
    "before_after_comparison",
    "ranked_extremes_comparison",
    "volatility_comparison",
    "distribution_comparison",
    "relationship_comparison",
    "median_comparison",
    "average_comparison"
]

def run_comparison_analysis(df,question,data_planner,dataset_context):
    num_groups=df[data_planner['date_grain']].nunique()
    # STEP 1 derive plan
    results=user_intent.comparison_method_intent(question,data_planner['date_grain'],num_groups,COMPARISON_ROUTING_PRIORITY,COMPARISON_STATS_PLAN)
    comparison_type, statistical_test = results.split(",")

    #STEP 2 conduct appropriate test
    if statistical_test=='welch_ttest':
        descriptive_statistics,welch_ttest_results=analysis.welch_ttest(df,data_planner['date_grain'])

    #TO-DO: INSERT OTHER TESTS

    #STEP 3 send results to claude & return string
    return summaries.run_comparison_analysis(question,dataset_context,comparison_type,statistical_test,df,descriptive_statistics,welch_ttest_results)