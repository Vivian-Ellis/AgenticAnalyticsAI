import sys
sys.path.append("../src/")
from plan.DataPipeline import DataLoader,ClaudeDataPlanBuilder

from Tools import charts_registry
from Tools.registries import analytics_tool_registry
from Tools.registries import chart_tool_registry

from Tools import analytics_registry
# import analytics_registry
# sys.path.append("../src/Orcestrator")
from Orcestrator.agent_response import AgentResponse
from Orcestrator.agent_validation import AgentValidator
import Narration.summaries as summaries

def run_analytics_agent(question,chat_history=None):
    chat_history = chat_history or []

    # data_plan = DataPlanBuilder(question).run()
    data_plan=ClaudeDataPlanBuilder(question).run()
    # AgentValidator.validate_plan(data_plan)

    data_loader = DataLoader(data_plan)
    df=data_loader.run()
    # AgentValidator.validate_data(data_loader)

    tool = analytics_tool_registry.get_tool(data_loader.data_plan.question_intent)
    # AgentValidator.validate_tool(tool, data_loader)

    result = tool["function"](data_loader)
    # AgentValidator.validate_result(result)

    chart_type = tool["default_chart"]
    chart = charts_registry.Chart(result, chart_type)
    chart_path = chart.run()

    return AgentResponse(question, result, chart_path, data_plan, tool)

def run_general_agent(question,metadata,chat_history=None):
    return summaries.run_general_assistant(question,metadata,chat_history)