import sys
sys.path.append("../src")
import analysis
import summaries
from scipy.stats import shapiro
import numpy as np

SPEARMAN_REASON=[]
CORR_METHOD='pearson'

def update_CORR_METHOD(value):
    global CORR_METHOD
    CORR_METHOD = value

def update_SPEARMAN_REASON(value):
    global SPEARMAN_REASON
    SPEARMAN_REASON.append(value)

def shapiro_normality_test(data):
    # The Shapiro-Wilk will be used to test for normailty where:
    # H_0 : the sample is drawn from a normally distributed population
    # H_1 : the sample is drawn from a population that is not normally distributed
    # Let the threshold for significance be 0.01 so that if p_value < 0.01, I rejected the null hypothesis and conclude that the data is not normally distributed.
    stat, p = shapiro(data)
    # print('Statistics=%.3f, p=%.5f' % (stat, p))
    # let the significance level be 0.01
    alpha = 0.01
    if p > alpha: #fail to reject null hypothesis, normal
        # print('normally distributed (fail to reject the H_0)')
        return True
    else: #reject null hypothesis, not normal.
        # print('NOT normally distributed (reject the H_0)')
        return False

def find_outliers(data):
    Q1 = data.quantile(0.25)
    Q3 = data.quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    outliers = data[(data < lower_bound) | (data > upper_bound)]
    return len(outliers)

def calculate_correlation(compare_df,DATA_PLANNER):
    numeric_df = compare_df.select_dtypes(include=[np.number])
    for series in DATA_PLANNER['series_ids']:
        # if any outliers switch to spearman
        if find_outliers(compare_df[series]) > 0:
            update_CORR_METHOD("spearman")
            update_SPEARMAN_REASON(f"{series} contained detected outliers.")

        # if non-noraml switch to spearman
        if shapiro_normality_test(compare_df[series]) == False:
            update_CORR_METHOD("spearman")
            update_SPEARMAN_REASON(f"{series} violated the configured normality threshold.")

    corr_df=numeric_df.corr(method=CORR_METHOD)
    corr_df.index.name = None
    return corr_df

def run_correlation_analysis(df,question,DATA_PLANNER,dataset_context):
    # STEP 1 get the aggregate df
    stats_df=analysis.compute_df_aggregation(df,group_by_fields=["series_id",DATA_PLANNER['date_grain']],computation="mean")
    # STEP 2 create the wide df
    compare_df=analysis.compare_series(df,index_field="date",columns_field="series_id",value_field="value")
    # STEP 3 compute appropriate correlation
    corr_df=calculate_correlation(compare_df,DATA_PLANNER)

    #STEP 4 send results to claude & return string
    if CORR_METHOD=='pearson':
        return summaries.run_pearson_correlation_analysis(question,dataset_context,corr_df,stats_df)
    if CORR_METHOD=='spearman':
        spearman_reason="\n".join(SPEARMAN_REASON)
        return summaries.run_spearman_correlation_analysis(question,dataset_context,corr_df,stats_df,spearman_reason)
