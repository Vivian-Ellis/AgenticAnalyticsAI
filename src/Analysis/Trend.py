import sys
sys.path.append("../src/")

import Analysis.analysis as analysis
import Narration.summaries as summaries
import DataBase.semantics as semantics
from Analysis.AnalysisResults import TrendResult
import numpy as np
from scipy.stats import linregress

class TrendAnalysis:
    def __init__(self,data_loader):
        self.summary_narration=None
        self.trends_df=None
        self.metrics=None
        self.series_semantics=None
        self.data_loader=data_loader

    def run_analysis(self):
        df=self.data_loader.data.copy()

        # STEP 1 understand dataset semantics
        self.series_semantics=semantics.dataset_ranking_semantics(self.data_loader.data_plan.series_ids)

        # STEP 2 METRICS -----------------------
        y='value'
        x='date'

        # Total percent change from start date to end date
        total_percent_change_start_end = ((df[y].iloc[-1] - df[y].iloc[0]) / df[y].iloc[0]) * 100

        # year-over-year change
        df = df.sort_values(x)
        df["yoy_change"] = (df["value"].pct_change(12) * 100)
        avg_yoy_change = df["yoy_change"].mean()

        #volatility
        volatility = df["value"].pct_change().std()

        if volatility < 0.005:
            volatility_level = "low"
        elif volatility < 0.02:
            volatility_level = "moderate"
        else:
            volatility_level = "high"

        # Linear trend
        reg_x = np.arange(len(df))
        reg_y = df["value"]
        reg = linregress(reg_x, reg_y)
        slope = reg.slope
        r_squared = reg.rvalue ** 2

        linear_trend_strength = "weak"
        if r_squared >= .9:
            linear_trend_strength = "very strong"
        elif r_squared >= .75:
            linear_trend_strength = "strong"
        elif r_squared >= .5:
            linear_trend_strength = "moderate"

        slope_direction = (
            "upward" if slope > 0
            else "downward" if slope < 0
            else "flat")

        self.metrics = {
            "slope_direction":slope_direction,
            "linear_trend_strength":linear_trend_strength,
            'volatility':volatility_level,
            "total_percent_change_start_end": round(total_percent_change_start_end, 2),
            "average_yoy_change": round(avg_yoy_change, 2),
            "volatility":volatility}

        self.trends_df = (
            df.groupby("YEAR")
            .agg(avg_value=("value","mean")).reset_index())

        self.trends_df["annual_growth_pct"] = (
            self.trends_df["avg_value"]
            .pct_change() * 100)
        
        #STEP 3 send results to claude & return string
        self.summary_narration=summaries.run_trend_analysis(self.metrics,self.trends_df,self.series_semantics)
        
        return TrendResult(
                    question=self.data_loader.data_plan.question,
                    intent=self.data_loader.data_plan.question_intent,
                    series_ids=self.data_loader.data_plan.series_ids,
                    date_grain=self.data_loader.data_plan.date_grain,
                    summary_narration=self.summary_narration,
                    metrics=self.metrics,
                    original_df=df,
                    trends_df=self.trends_df,
                    series_semantics=self.series_semantics)