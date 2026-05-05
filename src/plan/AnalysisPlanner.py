import sys
sys.path.append("../src/Analysis")

import Comparison,Ranking,Correlation

class AnalysisPlanner:
    def __init__(self,data_loader):
        self.data_loader=data_loader
        self.analysis_registry = {
            "correlation": Correlation.CorrelationAnalysis(data_loader),
            "ranking": Ranking.RankingAnalysis(data_loader),
            "comparison": Comparison.ComparisonAnalysis(data_loader)
        }
        self.analysis_results=None

    def run(self):
        intent = self.data_loader.data_plan.question_intent
        analysis_obj = self.analysis_registry[intent]
        self.analysis_results=analysis_obj.run_analysis()
        return self.analysis_results