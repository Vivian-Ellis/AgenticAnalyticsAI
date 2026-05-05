import sys
sys.path.append("../src")
from plan.DataPipeline import DataPlanBuilder,DataLoader
from Analysis import Charts
import tool_registry
import analytics_registry
# sys.path.append("../src/Orcestrator")
from Orcestrator.agent_response import AgentResponse
from Orcestrator.agent_validation import AgentValidator

def run_agent(question):
    data_plan = DataPlanBuilder(question).run()
    AgentValidator.validate_plan(data_plan)

    data_loader = DataLoader(data_plan)
    df=data_loader.run()
    AgentValidator.validate_data(data_loader)

    tool = tool_registry.get_tool(data_loader.data_plan.question_intent)
    AgentValidator.validate_tool(tool, data_loader)

    result = tool["function"](data_loader)
    AgentValidator.validate_result(result)

    chart_type = tool["default_chart"]
    chart = Charts.Chart(result, chart_type)
    chart_path = chart.run()

    return AgentResponse(question, result, chart_path, data_plan, tool)