import sys
sys.path.append("../src")
import db
import summaries
import user_intent

class DataPlanBuilder:
    def __init__(self,question):
        self.question=question
        self.question_intent=None
        self.series_ids=None
        self.date_grain=None
        self.start_date=None
        self.end_date=None
        self.dataset_context=None

    def determine_question_intent(self):
        #determine question intent via logreg
        self.question_intent=user_intent.predict_intent(self.question)

    def infer_query_parameters(self):
        #determine what dataset to use via fuzzywuzzy
        metadata=db.get_series_metadata()
        series_ids=user_intent.predict_series_intent(self.question,metadata)

        #determine the date aggregation grain
        date_grain=user_intent.date_aggregation_grain_intent(self.question)

        #determine time frame of dataset via claude LLM & validate output
        start_date, end_date=user_intent.timeline_intent(self.question,date_grain)
        
        self.series_ids=series_ids
        self.date_grain=date_grain
        self.start_date=start_date
        self.end_date=end_date
        
    def infer_data_context(self):
        #pull the series metadata
        self.dataset_context=summaries.build_context(self.series_ids)
        
    def run(self):
        self.determine_question_intent()
        self.infer_query_parameters()
        self.infer_data_context()
        
        return self
    
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
