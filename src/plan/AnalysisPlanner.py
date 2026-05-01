import sys
sys.path.append("../src/")

from Analysis import Comparison,Ranking,Correlation

class AnalysisPlanner:
    def __init__(self,data_loader):
        self.data_loader=data_loader
        self.analysis_registry = {
            "correlation": Correlation.CorrelationAnalysis(data_loader),
            "ranking": Ranking.RankingAnalysis(data_loader),
            "comparison": Comparison.ComparisonAnalysis(data_loader,alpha=0.05)
        }

    def run(self):
        intent = self.data_loader.data_plan.question_intent
        analysis_obj = self.analysis_registry[intent]
        return analysis_obj.run_analysis()

