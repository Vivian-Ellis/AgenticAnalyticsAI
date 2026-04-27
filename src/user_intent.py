import joblib
import sys
sys.path.append("../src")
import db
from fuzzywuzzy import process
import summaries
import date_parser

# Load from the saved file
QUESTION_INTENT_MODEL = joblib.load('../data/log_regression_intent_classifier.joblib')

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
    # Make a prediction
    return QUESTION_INTENT_MODEL.predict([question])[0]

def predict_series_intent(question,metadata):
    """
    this function uses fuzzywuzzy to determine which dataset to perform and analysis on.

    this function will return at most 3 of the highest matching datasets to use. 
    returns only the list of series_id of the datasets
    """
    metadata["search_text"] = (metadata["series_id"] + " " + metadata["title"])

    choice_map = dict(zip(metadata["search_text"], metadata["series_id"]))
    choices = metadata["search_text"].tolist()

    results = process.extract(question,choices,limit=3)

    top_results=[]
    for match, score in results:
        if score > 70:
            top_results.append(choice_map[match])

    return top_results

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