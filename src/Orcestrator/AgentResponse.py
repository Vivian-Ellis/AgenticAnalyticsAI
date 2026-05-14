import sys
sys.path.append("../src")

class AgentResponse:
    def __init__(self,question,result,chart_path,data_plan,tool):
        self.response = {
            "question": question,
            "status": "success",
            "summary": result.summary_narration,
            "chart_path": chart_path,
            "table": select_display_table(result),
            "original_table":result.original_df,
            "methodology_reasoning": select_methodology_reasoning(result),
            "data_plan": {
                "question_analytical_intent": data_plan.question_intent,
                "series_ids": data_plan.series_ids,
                "date_grain": data_plan.date_grain,
                "start_date": data_plan.start_date,
                "end_date": data_plan.end_date,
                "tool_name": tool["name"],
                "output_type": tool["output_type"],
                "default_chart": tool["default_chart"]
            }
        }

def select_methodology_reasoning(result):
    if result.question_analytical_intent == "ranking":
        return ""
    if result.question_analytical_intent == "comparison":
        return ""
    if result.question_analytical_intent == "correlation":
        return result.spearman_reason

def select_display_table(result):
    if result.question_analytical_intent == "ranking":
        return result.ranked_df
    if result.question_analytical_intent == "comparison":
        return result.descriptive_statistics
    if result.question_analytical_intent == "correlation":
        return result.corr_df
