from dataclasses import dataclass
from typing import Optional
import pandas as pd

@dataclass
class BaseResult:
    question: str
    intent: str
    series_ids: list[str]
    date_grain: str
    original_df:pd.DataFrame
    summary_narration: str

@dataclass
class RankingResult(BaseResult):
    ranked_df: pd.DataFrame
    ascending: bool
    n: int
    series_semantics: str
    method: str = "ranking"

@dataclass
class ComparisonResult(BaseResult):
    descriptive_statistics: pd.DataFrame
    comparison_type: str
    statistical_test: str
    inferential_statistics: object
    alpha:float
    method: str = "comparison"

@dataclass
class CorrelationResult(BaseResult):
    corr_df: pd.DataFrame
    corr_method: str
    spearman_reason: Optional[list[str]] = None
    method: str = "correlation"