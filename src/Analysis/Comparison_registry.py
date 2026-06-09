from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.append(str(SRC_DIR))

import Narration.summaries as summaries
import pandas as pd
import scipy.stats as stats
from scipy import stats
from scipy.stats import mannwhitneyu,kruskal,levene
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from Analysis.AnalysisResults import ComparisonResult

from pathlib import Path
from dotenv import load_dotenv
import sys

env_path = PROJECT_ROOT / ".env"
load_dotenv(env_path, override=True)

from Analysis.registry.Comparison_tool_registry import register_comparison

@register_comparison(
    "volatility_comparison",
    description="""Use this when the user wants to compare variability, volatility,
    fluctuations, stability, consistency, dispersion, or uncertainty
    between 2 or more groups.

    Use this for questions about:
    - which group is more volatile
    - which period is more stable
    - variability before vs after an event
    - fluctuations across years, quarters, or months
    - consistency of values across groups
    - dispersion or spread around typical values

    Example triggers:
    - Which year had the most volatile inflation?
    - Was unemployment more stable before or after COVID?
    - Compare fluctuations in interest rates between decades.
    - Which period shows the greatest variability?
    - Was inflation more consistent in the 2010s or 2020s?

    Do not use this when the user is asking to compare averages,
    medians, rankings, correlations, or distribution shapes.""",
    input_schema={
        "type": "object",
        "required": []
    }
)
def volatility_comparison(df,data_loader,num_groups):
    descriptive_statistics=df.groupby(data_loader.data_plan.date_grain).agg(variance=("value","var"),
                                                                            std_dev=("value","std"),
                                                                            mean=("value","mean")
                                                                            ).reset_index()
    descriptive_statistics['coefficient_of_variation']=descriptive_statistics["std_dev"]/descriptive_statistics["mean"]
    descriptive_statistics["Value"] = descriptive_statistics["std_dev"] #for charting purposes

    statistical_test="levene_test"
    groups=[]
    for g in df[data_loader.data_plan.date_grain].unique():
        groups.append(df[df[data_loader.data_plan.date_grain]==g]["value"])
    stats_test_results=levene(*groups)

    return descriptive_statistics, stats_test_results,statistical_test  

@register_comparison(
    "median_comparison",
    description="""Use this only when the user explicitly says median, medians, non-parametric,
rank-based, or asks to use median instead of average/mean.

Do not use this for vague words like typical, usual, normal, common,
representative, central, or generally higher/lower. Those should use
average_comparison unless the user explicitly says median.""",
    input_schema={
        "type": "object",
        "required": []
    }
)
def median_comparison(df,data_loader,num_groups):
    if num_groups==2:
        descriptive_statistics, stats_test_results=mann_whitney_u(df,data_loader)
        statistical_test="mann_whitney_u"
    elif num_groups > 2:
        descriptive_statistics, stats_test_results=kruskal_wallis(df,data_loader)
        statistical_test="kruskal_wallis"

    return descriptive_statistics, stats_test_results,statistical_test  

def mann_whitney_u(df,data_loader):
    descriptive_statistics=df.groupby(data_loader.data_plan.date_grain).agg(Value=("value","median")).reset_index()
    groups=[]
    for g in df[data_loader.data_plan.date_grain].unique():
        groups.append(df[df[data_loader.data_plan.date_grain]==g]["value"])
    # Conduct mannwhitneyu and return/save the result
    mannwhitneyu_results=mannwhitneyu(groups[0], groups[1])
    return descriptive_statistics,mannwhitneyu_results

def kruskal_wallis(df,data_loader):
    descriptive_statistics=df.groupby(data_loader.data_plan.date_grain).agg(Value=("value","median")).reset_index()
    groups=[]
    for g in df[data_loader.data_plan.date_grain].unique():
        groups.append(df[df[data_loader.data_plan.date_grain]==g]["value"])
    # Conduct kruskal and return/save the result
    kruskal_results=kruskal(*groups)
    return descriptive_statistics,kruskal_results


@register_comparison(
    "average_comparison",
    description="""Default comparison tool for comparing group levels, rates, values, averages,
means, or general central tendency between 2 or more groups.

Use this for vague comparison terms like typical, usual, common, normal,
representative, generally higher, generally lower, or overall level when the
user does not explicitly request median, volatility, distribution shape, or correlation.""",
    input_schema={
        "type": "object",
        "required": []
    }
)
def average_comparison(df,data_loader,num_groups):
    if num_groups==2:
        descriptive_statistics, stats_test_results=welch_ttest(df,data_loader)
        statistical_test="welch_ttest"
    elif num_groups > 2:
        descriptive_statistics, stats_test_results=one_way_anova(df,data_loader)
        statistical_test="one_way_anova"

    return descriptive_statistics, stats_test_results,statistical_test

def welch_ttest(df,data_loader):
    descriptive_statistics=df.groupby(data_loader.data_plan.date_grain).agg(Value=("value","mean")).reset_index()
    groups=[]
    for g in df[data_loader.data_plan.date_grain].unique():
        groups.append(df[df[data_loader.data_plan.date_grain]==g]["value"])
    # Conduct Welch's t-Test and return/save the result
    welch_ttest_results=stats.ttest_ind(groups[0], groups[1], equal_var = False)
    return descriptive_statistics,welch_ttest_results

def one_way_anova(df,data_loader,alpha=.05):
    anova_results = {
        "f_stat": None,
        "p_value": None,
        "alpha": alpha,
        "tukey": None
    }

    descriptive_statistics = (
        df.groupby(data_loader.data_plan.date_grain)
        .agg(Value=("value", "mean"))
        .reset_index()
    )
    groups=[]
    for g in df[data_loader.data_plan.date_grain].unique(): 
        groups.append(df[df[data_loader.data_plan.date_grain]==g]["value"]) 
    
    f_stat, p_value = stats.f_oneway(*groups)

    anova_results["f_stat"] = f_stat
    anova_results["p_value"] = p_value

    if p_value <= alpha:
        tukey = pairwise_tukeyhsd(
            endog=df["value"],
            groups=df[data_loader.data_plan.date_grain],
            alpha=alpha
        )
        tukey_df = pd.DataFrame(
            data=tukey._results_table.data[1:],
            columns=tukey._results_table.data[0]
        )
        anova_results["tukey"] = tukey_df
    return descriptive_statistics, anova_results