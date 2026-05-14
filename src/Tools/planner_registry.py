import joblib
import sys
sys.path.append("../src")
import DataBase.db as db
# from fuzzywuzzy import process
import Narration.summaries as summaries
import date_parser
from Tools.registries.planner_tool_registry import register_planner_tool
import pandas as pd
pd.set_option('display.max_colwidth', None)

import os
import joblib

BASE_DIR = os.path.dirname(__file__)

MODEL_PATH = os.path.abspath(
    os.path.join(
        BASE_DIR,
        "..",
        "..",
        "data",
        "log_regression_intent_classifier.joblib"
    )
)

QUESTION_INTENT_MODEL = joblib.load(MODEL_PATH)

SERIES_ALIASES = {
    "CPIAUCSL": ["inflation","cpi","consumer price index","prices"],
    "UNRATE": ["jobless","unemployment"],
    "FEDFUNDS": ["interest","federal funds"],
    "GDP": ["economic output","gdp","gross domestic product"],
    "PAYEMS": ["jobs","payrolls","nonfarm","household employees", "unpaid volunteers", "farm employees", "self-employed"]
}

def rule_based_intent_override(question):
    q = question.lower()

    comparison_terms = ["difference","different","compare", "compared","between", "higher than","lower than","before and after","before","after"]
    correlation_terms = ["relationship","correlation","correlated","association","move together","related"]
    ranking_terms = ["top","bottom", "highest", "lowest", "rank","worst", "best"]

    if any(term in q for term in ranking_terms):
        return "ranking"
    if any(term in q for term in correlation_terms):
        return "correlation"
    if any(term in q for term in comparison_terms):
        return "comparison"

    return None

@register_planner_tool(
    "predict_analytical_intent",
    description="Selects the best analytical intent for the user question.",
    input_schema={
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The user's most recent analytical question."
            }
        },
        "required": ["question"]
    },
    output_type="str"
)
def predict_analytical_intent(question):
    """
    this function will predict the analytical intent of the question. 
    the following categories are options: 
    QUESTION_CATEGORIES = ["trend",
                            "comparison",
                            "ranking",
                            "volatility",
                            "correlation",
                            "unsupported"]

    this function uses a pretrained logistic regression model from data\log_regression_intent_classifier.joblib 
    with the latest accuracy of 93% returns one of the above categories
    """
    override = rule_based_intent_override(question)
    if override is not None:
        return override
    # Make a prediction using ml model
    return QUESTION_INTENT_MODEL.predict([question])[0]

@register_planner_tool(
    "predict_series_intent",
    description="Selects the best FRED series IDs for the user question.",
    input_schema={
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The user's most recent analytical question."
            }
        },
        "required": ["question"]
    },
    output_type="list[str]"
)
def predict_series_intent(question):
    """
    this function uses LLM to determine which dataset to perform and analysis on.

    this function will return the highest matching datasets to use. 
    returns only the list of series_id of the datasets
    """
    top_results=[]
    metadata = db.get_series_metadata()
    metadata["aliases"] = metadata["series_id"].map(lambda x: " ".join(SERIES_ALIASES.get(x, [])))    
    metadata["search_text"] = (metadata["series_id"] + " " + metadata["title"]+" "+metadata["aliases"])
    inferred_series_intent = summaries.run_series_intent_prompt(question)
    top_results.extend(inferred_series_intent.split(','))
    return top_results


@register_planner_tool(
    "timeline_intent",
    description="Selects the best date range for the user question.",
    input_schema={
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The user's most recent analytical question."
            }
        },
        "required": ["question","date_grain"]
    },
    output_type="str"
)
def timeline_intent(question,date_grain):
    """
    this function uses claude LLM to determine a date range for the user question

    this function also performs validation of the LLM results and if validation fails the 
    LLM will attempt to extract the date again. If the LLM cannot find a vlaid date we will
    use "2016-01-01" thru last time FRED data was updated
    
    returns a start and end date in the format YYYY-MM-DD to be used to filter a df down
    """
    metadata=db.run_query("SELECT max(observation_end) as last_observation_date FROM raw_fred_metadata")
    last_observation_date=metadata['last_observation_date'][0]
    prompt=summaries.build_timeframe_prompt(question,last_observation_date,date_grain)
    date_range= summaries.run_prompt(prompt)
    #validate the dates
    start_date, end_date = date_parser.validate_date(date_range)

    if start_date is None or end_date is None:
        new_date_range = timeline_intent_failed(question, date_range)
        start_date, end_date = date_parser.validate_date(new_date_range)

        if start_date is None or end_date is None:
            start_date = "2016-01-01"
            end_date = last_observation_date

    return start_date, end_date

def timeline_intent_failed(question,date_range):
    prompt=summaries.timeframe_validation_failed_prompt(question,date_range)
    return summaries.run_prompt(prompt)

@register_planner_tool(
    "date_aggregation_grain_intent",
    description="Selects the best date grain (aggresgation on the date field) for the users question. Is one of the following: 'DAY','WEEK','MONTH','QUARTER','YEAR','YEAR_MONTH'",
    input_schema={
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The user's most recent analytical question."
            }
        },
        "required": ["question","date_grain"]
    },
    output_type="str"
)
def date_aggregation_grain_intent(question):
    date_grain=summaries.run_prompt(summaries.build_timeframe_aggregation_prompt(question))
    #quick validation
    if date_grain in ['DAY','WEEK','MONTH','QUARTER','YEAR','YEAR_MONTH']:
        return date_grain
    else:
        return 'YEAR'