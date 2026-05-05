import sys
sys.path.append("../src")
from plan.DataPipeline import DataPlanBuilder,DataLoader
from Analysis import Charts
import tool_registry

class AgentResponse:
    def __init__(self,question,result,chart_path,data_plan,tool):
        self.response = {
            "question": question,
            "status": "success",
            "summary": result.summary_narration,
            "chart_path": chart_path,
            "table": select_display_table(result),
            "metadata": {
                "intent": data_plan.question_intent,
                "series_ids": data_plan.series_ids,
                "date_grain": data_plan.date_grain,
                "start_date": data_plan.start_date,
                "end_date": data_plan.end_date,
                "tool_name": tool["name"],
                "output_type": tool["output_type"],
                "default_chart": tool["default_chart"]
            }
        }

def select_display_table(result):
    if result.intent == "ranking":
        return result.ranked_df

    if result.intent == "comparison":
        return result.descriptive_statistics

    if result.intent == "correlation":
        return result.corr_df
 
