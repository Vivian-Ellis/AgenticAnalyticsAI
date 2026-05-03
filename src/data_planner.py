import sys
sys.path.append("../src")
import DataBase.db as db
import Narration.summaries as summaries
import user_intent
import time

def build_data_plan(question):
    # ---------------------DATA PLAN-----------------
    # STEP 1 determine question intent via logreg
    question_intent=user_intent.predict_intent(question)

    # STEP 2 determine what dataset to use via fuzzywuzzy
    metadata=db.get_series_metadata()
    series_ids=user_intent.predict_series_intent(question,metadata)

    # STEP 3 determine the date aggregation grain
    date_grain=user_intent.date_aggregation_grain_intent(question)

    # STEP 4 determine time frame of dataset via claude LLM & validate output
    start_date, end_date=user_intent.timeline_intent(question,date_grain)

    DATA_PLANNER={
    "question_intent":question_intent,
    "series_ids":series_ids,
    "date_grain":date_grain,
    "start_date":start_date,
    "end_date":end_date
    }

    # ---------------------DATA PREPERATION-----------------
    # STEP 5 pull the series metadata
    dataset_context=summaries.build_context(series_ids)

    # STEP 6 pull relevant data (does the limiting and pulls date grain needed for aggergation)
    series_sql = ",".join(f"'{x}'" for x in DATA_PLANNER["series_ids"])
    query=f"""SELECT *,EXTRACT({DATA_PLANNER["date_grain"]} from date) as '{DATA_PLANNER["date_grain"]}' 
    FROM clean_fred_data 
    WHERE series_id in ({series_sql}) 
    and date between '{DATA_PLANNER["start_date"]}' and '{DATA_PLANNER["end_date"]}'"""
    df=db.run_query(query)
    
    return df,dataset_context,DATA_PLANNER