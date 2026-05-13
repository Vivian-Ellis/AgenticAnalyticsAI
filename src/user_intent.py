import joblib
import sys
sys.path.append("../src")
import DataBase.db as db
from fuzzywuzzy import process
import Narration.summaries as summaries
import date_parser

import pandas as pd
pd.set_option('display.max_colwidth', None)

import os
import joblib

BASE_DIR = os.path.dirname(__file__)

MODEL_PATH = os.path.abspath(
    os.path.join(
        BASE_DIR,
        "..",
        "data",
        "log_regression_intent_classifier.joblib"
    )
)

QUESTION_INTENT_MODEL = joblib.load(MODEL_PATH)

# # Load from the saved file
# QUESTION_INTENT_MODEL = joblib.load('../data/log_regression_intent_classifier.joblib')

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

def predict_intent(question):
    """
    this function will predict the analytical intent of the question. 
    the following categories are options: 
    QUESTION_CATEGORIES = [
    "trend",
    "comparison",
    "ranking",
    "volatility",
    "correlation",
    "unsupported"
    ]

    this function uses a pretrained logistic regression model from data\log_regression_intent_classifier.joblib with the latest accuracy of 93%

    returns one of the above categories
    """
    override = rule_based_intent_override(question)
    if override is not None:
        return override
    
    # Make a prediction using ml model
    return QUESTION_INTENT_MODEL.predict([question])[0]

def predict_series_intent(question,metadata):
    """
    this function uses fuzzywuzzy to determine which dataset to perform and analysis on.

    this function will return at most 3 of the highest matching datasets to use. 
    returns only the list of series_id of the datasets
    """
    top_results=[]

    # question_lower = question.lower()

    # for series_id, aliases in SERIES_ALIASES.items():
    #     # check series_id itself
    #     if series_id.lower() in question_lower:
    #         top_results.append(series_id)
    #         continue

    #     # check aliases
    #     for alias in aliases:
    #         if alias.lower() in question_lower:
    #             top_results.append(series_id)
    #             break

    # now perform fuzzy matching
    metadata["aliases"] = metadata["series_id"].map(lambda x: " ".join(SERIES_ALIASES.get(x, [])))    
    metadata["search_text"] = (metadata["series_id"] + " " + metadata["title"]+" "+metadata["aliases"])
    choice_map = dict(zip(metadata["search_text"], metadata["series_id"]))
    choices = metadata["search_text"].tolist()

    results = process.extract(question,choices,limit=5)
    # for match, score in results:
    #     if score > 70 and choice_map[match] not in top_results:
    #         top_results.append(choice_map[match])

    # if len(top_results) ==0:
    print(results)
    clarification_results=series_intent_clarification(question,results)
    print(clarification_results)
    top_results.extend(clarification_results)
    return top_results

def series_intent_clarification(question,fuzzywuzzy):
    #     fuzzywuzzy was used to calculate the best possible dataset matches:
    # {fuzzywuzzy}
    clarification_prompt = f""" The user asked:{question}

    The system needs clarification on which dataset to use based on the user inquiry and the data semantics:

    Dataset semantic mappings:

    - inflation, cpi, prices, consumer price index -> CPIAUCSL
    - unemployment, unemployed, jobless, joblessness -> UNRATE
    - employment, employed, jobs, payrolls, workforce, labor market, workers -> PAYEMS
    - interest rates, interest, federal funds, fed funds, monetary policy -> FEDFUNDS
    - gdp, economic output, gross domestic product -> GDP

    Important semantic rules:

    - "employment" is NOT the same as "unemployment"
    - questions about workers, jobs, or employment levels should use PAYEMS
    - questions about joblessness or unemployment rates should use UNRATE
    - use multiple dataset codes if the question compares multiple economic concepts

    Based on the semanitic meanings which dataset should I use to best answer the users question? 
    
    Output Rules:
    - Return ONLY a comma seperated list [CPIAUCSL,UNRATE,FEDFUNDS,GDP,PAYEMS]
    - No spaces
    - No explanations
    - Do not include labels, explanations, bullets, or additional text. 
    """
    message = summaries.run_prompt(clarification_prompt)
    return message.split(',')

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

def date_aggregation_grain_intent(question):
    date_grain=summaries.run_prompt(summaries.build_timeframe_aggregation_prompt(question))
    #quick validation
    if date_grain in ['DAY','WEEK','MONTH','QUARTER','YEAR','YEAR_MONTH']:
        return date_grain
    else:
        return 'YEAR'
    
def comparison_method_intent(question,date_grain,num_groups,routing_priority,stat_test_plan):
    prompt=summaries.build_comparison_method_prompt(question,date_grain,num_groups,routing_priority,stat_test_plan)
    return summaries.run_prompt(prompt)