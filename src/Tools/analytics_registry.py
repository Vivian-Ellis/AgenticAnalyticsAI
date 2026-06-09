import Analysis.Comparison as Comparison
import Analysis.Ranking as Ranking
import Analysis.Correlation as Correlation
from Tools.registries.analytics_tool_registry import register_analytics_tool

@register_analytics_tool(
    "ranking",
    description="""Performs ranking analysis by interpreting the semantic intent of a ranking question, 
        determining the appropriate ranking direction and number of results, aggregating the dataset, and 
        ranking grouped periods by the calculated metric. Generates a narrated summary of the ranked results 
        and returns a structured `RankingResult` object containing the rankings, metadata, and analysis outputs.""",
    input_schema={
        "type": "object",
        "properties": {
            "data_loader": {
                "type": "object",
                "description": "DataLoader object containing a DataPlan (from DataPlanBuilder) and analysis-ready metadata."
            }
        },
        "required": ["data_loader"]
    },
    default_chart="ranking_bar"
)
def ranking_tool(data_loader):
    """
    Run ranking analysis.
    """
    analysis = Ranking.RankingAnalysis(data_loader)
    return analysis.run_analysis()

@register_analytics_tool(
    "correlation",
    description="""Performs correlation analysis by reshaping and aggregating time series data, testing for 
    outliers and normality, and dynamically selecting either Pearson or Spearman correlation based on the 
    statistical properties of the data. Generates a narrated interpretation of the correlation results and 
    returns a structured `CorrelationResult` object containing the correlation matrix, selected method, 
    supporting diagnostics, and analysis outputs.""",
    input_schema={
        "type": "object",
        "properties": {
            "data_loader": {
                "type": "object",
                "description": "DataLoader object containing a DataPlan (from DataPlanBuilder) and analysis-ready metadata."
            }
        },
        "required": ["data_loader"]
    },
    default_chart="correlation_scatter"
)
def correlation_tool(data_loader):
    """
    Run correlation analysis.
    """
    analysis = Correlation.CorrelationAnalysis(data_loader)
    return analysis.run_analysis()

@register_analytics_tool(
    "comparison",
    description="""Performs statistical comparison analysis for questions that compare values across groups, periods, or event-defined cohorts.

Use this for questions asking whether one group, period, or cohort is higher, lower, greater, smaller, more, less, different, more stable, more volatile, or otherwise different from another.

Use this for questions asking whether groups differ in:
- averages, means, levels, or rates
- questions phrased as "higher in A or B", "lower in A or B", "more in A than B", "less in A than B", "A vs B", or "between A and B"
- medians, when explicitly requested
- variability, volatility, fluctuations, stability, consistency, or dispersion
- before/after or pre/post periods
- highest vs lowest, top vs bottom, or other grouped comparisons

Examples:
- Was inflation higher in 2018 or 2022 on average?
- Was unemployment lower in 2024 or 2025?
- Which year had higher average CPI, 2018 or 2022?
- Did unemployment differ between 2024 and 2025?
- Was inflation more volatile in 2022 than 2018?
- Compare median unemployment rates between 2024 and 2025.

The comparison analysis delegates to specialized comparison tools such as average_comparison, median_comparison, and volatility_comparison, then selects the appropriate statistical test based on the number of groups and comparison type. Examples include Welch’s t-test, one-way ANOVA, Mann-Whitney U, Kruskal-Wallis, and Levene’s test.

Do not use this for ranking-only questions or relationship/association questions between multiple variables; those should route to ranking or correlation.

Returns a structured `ComparisonResult` object containing the comparison type, statistical test used, descriptive statistics, inferential outputs, and generated analysis summary.""",
    input_schema={
        "type": "object",
        "properties": {
            "data_loader": {
                "type": "object",
                "description": "DataLoader object containing a DataPlan (from DataPlanBuilder) and analysis-ready metadata."
            }
        },
        "required": ["data_loader"]
    },
    output_type= "ComparisonResult",
    default_chart= "comparison_bar"
)
def comparison_tool(data_loader):
    """
    Run comparison analysis.
    """
    analysis = Comparison.ComparisonAnalysis(data_loader)
    return analysis.run_analysis()