import sys
sys.path.append("../src/Analysis")

import Comparison,Ranking,Correlation
from tool_registry import register_tool

@register_tool(
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

@register_tool(
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

@register_tool(
    "comparison",
    description="""Performs statistical comparison analysis by interpreting the semantic intent of a comparison question, 
    selecting the appropriate inferential statistical test (such as Welch’s t-test or one-way ANOVA), computing descriptive 
    and inferential statistics across grouped data, and generating a narrated interpretation of the results. Returns a structured 
    `ComparisonResult` object containing the comparison type, statistical test used, descriptive statistics, inferential outputs, 
    and generated analysis summary.""",
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