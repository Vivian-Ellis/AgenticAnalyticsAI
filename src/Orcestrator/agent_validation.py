import sys
sys.path.append("../src")
import tool_registry
import pandas as pd

class AgentValidator:
    VALID_INTENTS = {"ranking", "comparison", "correlation"}
    VALID_DATE_GRAINS = {"DAY", "MONTH", "QUARTER", "YEAR"}

    @staticmethod
    def validate_plan(data_plan):
        """
        Validate the DataPlanBuilder output before loading data.
        """
        if data_plan is None:
            raise ValueError("Data plan is None.")
        if not data_plan.question:
            raise ValueError("Data plan is missing the original question.")
        if data_plan.question_intent not in AgentValidator.VALID_INTENTS:
            raise ValueError(
                f"Unsupported question intent: {data_plan.question_intent}. "
                f"Expected one of {AgentValidator.VALID_INTENTS}.")
        if not data_plan.series_ids:
            raise ValueError("Data plan did not identify any series_ids.")
        if not isinstance(data_plan.series_ids, list):
            raise TypeError("data_plan.series_ids must be a list.")
        if data_plan.date_grain not in AgentValidator.VALID_DATE_GRAINS:
            raise ValueError(
                f"Invalid date_grain: {data_plan.date_grain}. "
                f"Expected one of {AgentValidator.VALID_DATE_GRAINS}.")
        if not data_plan.start_date or not data_plan.end_date:
            raise ValueError("Data plan must include both start_date and end_date.")
        if data_plan.start_date > data_plan.end_date:
            raise ValueError(
                f"Invalid date range: start_date {data_plan.start_date} "
                f"is after end_date {data_plan.end_date}.")
        return True

    @staticmethod
    def validate_data(data_loader):
        """
        Validate that DataLoader successfully loaded analysis-ready data.
        """
        if data_loader is None:
            raise ValueError("DataLoader is None.")
        if data_loader.data_plan is None:
            raise ValueError("DataLoader is missing data_plan.")
        if data_loader.data is None:
            raise ValueError("DataLoader did not load data. data_loader.data is None.")
        if not isinstance(data_loader.data, pd.DataFrame):
            raise TypeError("data_loader.data must be a pandas DataFrame.")
        if data_loader.data.empty:
            raise ValueError("DataLoader returned an empty DataFrame.")

        required_cols = {"date", "value", "series_id", data_loader.data_plan.date_grain}
        missing_cols = required_cols - set(data_loader.data.columns)
        if missing_cols:
            raise ValueError(f"Loaded data is missing required columns: {missing_cols}")
        if data_loader.data["value"].isna().all():
            raise ValueError("Loaded data has no usable numeric values.")

        return True

    @staticmethod
    def validate_tool(tool, data_loader):
        """
        Validate that the selected registered tool is usable for the loaded data.
        """
        if tool is None:
            raise ValueError("Tool is None.")
        if tool is NotImplementedError:
            raise ValueError(
                f"No registered tool found for intent: "
                f"{data_loader.data_plan.question_intent}")

        required_keys = {
            "name",
            "description",
            "input_schema",
            "function",
            "default_chart"}

        missing_keys = required_keys - set(tool.keys())
        if missing_keys:
            raise ValueError(f"Tool is missing required keys: {missing_keys}")

        if not callable(tool["function"]):
            raise TypeError(f"Tool function for {tool['name']} is not callable.")

        if tool["name"] != data_loader.data_plan.question_intent:
            raise ValueError(
                f"Tool name {tool['name']} does not match question intent "
                f"{data_loader.data_plan.question_intent}.")

        chart_tool = tool_registry.get_chart_tool(tool["default_chart"])
        if chart_tool is NotImplementedError:
            raise ValueError(
                f"No registered chart found for default_chart: {tool['default_chart']}")

        if data_loader.data_plan.question_intent == "correlation":
            if len(data_loader.data_plan.series_ids) < 2:
                raise ValueError(
                    "Correlation analysis requires at least two series_ids.")

        if data_loader.data_plan.question_intent == "comparison":
            num_groups = data_loader.data[data_loader.data_plan.date_grain].nunique()
            if num_groups < 2:
                raise ValueError(
                    "Comparison analysis requires at least two date groups.")

        return True

    @staticmethod
    def validate_result(result):
        """
        Validate that the analysis result object contains the fields needed downstream.
        """
        if result is None:
            raise ValueError("Analysis result is None.")
        base_attrs = [
            "question",
            "intent",
            "series_ids",
            "date_grain",
            "original_df",
            "summary_narration"]

        for attr in base_attrs:
            if not hasattr(result, attr):
                raise ValueError(f"Result is missing required attribute: {attr}")
        if not result.summary_narration:
            raise ValueError("Result is missing summary_narration.")
        if result.intent == "ranking":
            required_attrs = ["ranked_df", "ascending", "n", "series_semantics"]
        elif result.intent == "comparison":
            required_attrs = [
                "descriptive_statistics",
                "comparison_type",
                "statistical_test",
                "inferential_statistics",
                "alpha"]

        elif result.intent == "correlation":
            required_attrs = ["corr_df", "corr_method", "spearman_reason"]
        else:
            raise ValueError(f"Unsupported result intent: {result.intent}")
        for attr in required_attrs:
            if not hasattr(result, attr):
                raise ValueError(
                    f"{result.intent} result is missing required attribute: {attr}")

        return True