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
        date_grain=self.data_loader.data_plan.date_grain
        # STEP 2 METRICS -----------------------
        y='value'
        x='date'

        # Total percent change from start date to end date
        total_percent_change_start_end = ((df[y].iloc[-1] - df[y].iloc[0]) / df[y].iloc[0]) * 100

        # Total percent change from start date to end date
        total_percent_change_start_end = ((df[y].iloc[-1] - df[y].iloc[0]) / df[y].iloc[0]) * 100

        # CAGR (Annualized growth rate)
        num_years = df[date_grain].nunique()
        cagr = ((df[y].iloc[-1] / df[y].iloc[0]) ** (1 / num_years) - 1) * 100

        # CAGR (Annualized growth rate for recent years)
        num_recent_years=round(num_years*.1)
        if num_recent_years<1:
            num_recent_years=1

        recent_years=df[df[date_grain]>=(df[date_grain].max()-num_recent_years)]
        recent_years_cagr = ((recent_years['value'].iloc[-1] / recent_years['value'].iloc[0]) ** (1 / num_recent_years) - 1) * 100

        growth_regime = (
            "accelerating"
            if recent_years_cagr > cagr * 1.15
            else "decelerating"
            if recent_years_cagr < cagr * 0.85
            else "stable")

        # year-over-year change
        df = df.sort_values(x)
        df["yoy_change"] = (df["value"].pct_change(12) * 100)
        avg_yoy_change = df["yoy_change"].mean()

        #volatility
        volatility = df["value"].pct_change().std()

        # Linear trend
        reg_x = np.arange(len(df))
        reg_y = df["value"]
        reg = linregress(reg_x, reg_y)
        slope = reg.slope

        slope_direction = (
            "upward" if slope > 0
            else "downward" if slope < 0
            else "flat")

        # drawdown
        rolling_max = df[y].cummax()
        drawdown = ((df[y] - rolling_max)/ rolling_max)
        max_drawdown = drawdown.min() * 100

        # growth metrics
        if self.data_loader.data_plan.series_ids == 'CPIAUCSL':
            self.metrics={
                    "average_yoy_change": round(avg_yoy_change, 2),
                    "total_num_years":num_years,
                    "total_cagr": round(cagr, 2),
                    "recent_years_cagr":round(recent_years_cagr,2),
                    "num_recent_years_tracked_for_cagr":num_recent_years,
                    "growth_regime":growth_regime}
            
        elif self.data_loader.data_plan.series_ids == 'PAYEMS':
            self.metrics= {
                "total_num_years":num_years,
                "total_cagr": round(cagr, 2),
                "recent_years_cagr":round(recent_years_cagr,2),
                "num_recent_years_tracked_for_cagr":num_recent_years,
                "average_yoy_change": round(avg_yoy_change, 2),
                "slope_direction":slope_direction,
                "max_drawdown":max_drawdown}
            
        elif self.data_loader.data_plan.series_ids == 'GDP':  
            r_squared = reg.rvalue ** 2

            linear_trend_strength = "weak"
            if r_squared >= .9:
                linear_trend_strength = "very strong"
            elif r_squared >= .75:
                linear_trend_strength = "strong"
            elif r_squared >= .5:
                linear_trend_strength = "moderate"    

            self.metrics= {
                "total_num_years":num_years,
                "total_cagr": round(cagr, 2),
                "recent_years_cagr":round(recent_years_cagr,2),
                "num_recent_years_tracked_for_cagr":num_recent_years,
                "average_yoy_change": round(avg_yoy_change, 2),
                # "r_squared":r_squared,
                "trend_strength":linear_trend_strength,
                "max_drawdown":max_drawdown}
            
        elif self.data_loader.data_plan.series_ids == 'M2SL':     
            self.metrics= {
                "recent_years_cagr":round(recent_years_cagr,2),
                "total_cagr": round(cagr, 2),
                "average_yoy_change": round(avg_yoy_change, 2),
                "growth_regime":growth_regime}
            
        elif self.data_loader.data_plan.series_ids == 'SP500':     
            self.metrics= {
                "total_num_years":num_years,
                "total_cagr": round(cagr, 2),
                "recent_years_cagr":round(recent_years_cagr,2),
                "num_recent_years_tracked_for_cagr":num_recent_years,
                "max_drawdown":max_drawdown,
                "volatility":volatility,
                "slope_direction":slope_direction}
            
    # rate metrics
        elif self.data_loader.data_plan.series_ids == 'FEDFUNDS':
            self.metrics= {
                "total_percent_change_start_end": round(total_percent_change_start_end, 2),
                "slope":slope,
                "slope_direction":slope_direction,      
                "volatility":volatility,
                "growth_regime":growth_regime}
        
        elif self.data_loader.data_plan.series_ids == 'DGS10':
            self.metrics= {
                "slope":slope,
                "slope_direction":slope_direction,  
                "volatility":volatility,
                "max_drawdown":max_drawdown
            }
        elif self.data_loader.data_plan.series_ids == 'UNRATE':
            self.metrics= {
                "slope_direction":slope_direction,
                "total_percent_change_start_end": round(total_percent_change_start_end, 2),
                "volatility":volatility,
                "max_drawdown":max_drawdown
            }

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
