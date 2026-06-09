from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.append(str(SRC_DIR))

import Narration.summaries as summaries
import pandas as pd
import scipy.stats as stats
from scipy import stats
from Analysis.AnalysisResults import ComparisonResult

from Analysis.registry.Comparison_tool_registry import list_anthropic_comparison_tools,get_comparison_tool
from Analysis import Comparison_registry #need to import this because it populates the resigstry with all the tools in the script

class ComparisonAnalysis:
    def __init__(self,data_loader,alpha=0.05):
        self.summary_narration=None
        self.descriptive_statistics=None
        self.stats_test_results=None
        self.data_loader=data_loader
        self.alpha=alpha

    def run_analysis(self):
        user_input=self.data_loader.data_plan.question
        df=self.data_loader.data.copy()
        num_groups=df[self.data_loader.data_plan.date_grain].nunique()
        print(num_groups)
        comparison_tools = list_anthropic_comparison_tools()
        message = f"""You are a routing layer. You must call exactly one comparison tool.
        Do not answer the user directly.
        Do not ask clarifying questions.

        User message:
        {user_input}"""

        # STEP 1 derive plan via claude and the comparison tool registry
        # Claude chooses to call the tool
        message_content = summaries.run_tool_prompt(comparison_tools, message)
        comparison_type = None
        # Python executes the tool
        for block in message_content:
            if block.type == "tool_use":
                tool = get_comparison_tool(block.name)
                tool_input = dict(block.input)
                print(tool_input)
                comparison_type=block.name
                # inject Python-side objects
                tool_input["df"] = df
                tool_input["data_loader"] = self.data_loader
                tool_input["num_groups"] = num_groups
                #STEP 2 conduct appropriate test chosen by claude
                self.descriptive_statistics, self.stats_test_results,statistical_test = tool["function"](**tool_input)
                break
        if comparison_type is None:
            raise ValueError(f"Claude did not call a comparison tool. Response was: {message_content}")

        #STEP 3 send results to claude & return string
        self.summary_narration= summaries.run_comparison_analysis(self.data_loader.data_plan.question,
                                                self.data_loader.data_plan.dataset_context,
                                                comparison_type,
                                                statistical_test,
                                                df,
                                                self.descriptive_statistics,
                                                self.stats_test_results)

        return ComparisonResult(
        question=self.data_loader.data_plan.question,
        intent=self.data_loader.data_plan.question_intent,
        series_ids=self.data_loader.data_plan.series_ids,
        date_grain=self.data_loader.data_plan.date_grain,
        original_df=df,
        summary_narration=self.summary_narration,
        descriptive_statistics=self.descriptive_statistics,
        comparison_type=comparison_type,
        statistical_test=statistical_test,
        inferential_statistics=self.stats_test_results,
        alpha=self.alpha
    )