import sys
sys.path.append("../src/")
import DataBase.db as db
import Narration.summaries as summaries
import Tools.planner_registry as planner_registry
from pathlib import Path
import os
import anthropic

import joblib
import sys
sys.path.append("../src")

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

from Tools.registries.planner_tool_registry import list_anthropic_planner_tools,get_planner_tool
from Tools import planner_registry 
import Narration.summaries

class DataLoader:
    def __init__(self,data_plan):
        self.data=None
        self.data_plan=data_plan

    def load_data(self):
        #pull relevant data (does the limiting and pulls date grain needed for aggergation)
        series_sql = ",".join(f"'{x}'" for x in self.data_plan.series_ids)
        query=f"""SELECT *,EXTRACT({self.data_plan.date_grain} from date) as '{self.data_plan.date_grain}' 
        FROM clean_fred_data 
        WHERE series_id in ({series_sql}) 
        and date between '{self.data_plan.start_date}' and '{self.data_plan.end_date}'"""
        self.data=db.run_query(query)
        return self.data
        
    def run(self):
        return self.load_data()

class ClaudeDataPlanBuilder:
    def __init__(self,question):
        self.question=question
        self.planner_tools=list_anthropic_planner_tools()
        self.question_intent=None
        self.series_ids=None
        self.date_grain=None
        self.start_date=None
        self.end_date=None
        self.dataset_context=None

    # #this is only for the analytical intent
    # def build_data_plan(self):
    #     message=f"""I want to determine the analytical intent of the user's question. Choose the correct 
    #                 planner tool to call from the available tools. Build the tool call with the required arguments.
    #                 User question:
    #                 {self.question}
    #                 """
    #     message_content=summaries.run_tool_prompt(self.planner_tools,message)

    #     for block in message_content:
    #         if block.type == "tool_use":
    #             get_planner_tool(block.name)["function"](**block.input)

    def build_entire_data_plan(self):
        message=f"""Build the complete DataPlan for this analytics question.

                    The DataPlan must include:
                    - question_intent
                    - series_ids
                    - date_grain
                    - start_date
                    - end_date

                    Choose the best planner tool to build this plan.

                    User question:
                    {self.question}"""
        
        # Claude chooses to call the tool
        message_content=summaries.run_tool_prompt(self.planner_tools,message)
        # Python executes the tool
        for block in message_content:
            if block.type == "tool_use":
                tool = get_planner_tool(block.name)
                result = tool["function"](**block.input)

        if result is None:
            raise ValueError("Claude did not call a planner tool.")
    
        self.question_intent = result["question_intent"]
        self.series_ids = result["series_ids"]
        self.date_grain = result["date_grain"]
        self.start_date = result["start_date"]
        self.end_date = result["end_date"]
        self.dataset_context = result["dataset_context"]

        return self

    def run(self):
        return self.build_entire_data_plan()