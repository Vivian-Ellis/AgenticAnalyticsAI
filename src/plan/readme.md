# DataPipeline
The DataPipeline contains two main classes:

-DataLoader
-ClaudeDataPlanBuilder

## DataLoader
This class is used to connect to the fred duck DB and query data based on the current data plan. The `load_data` function will pull relevant data and perform any necessary limiting. The data will be limited based on the FRED series needed for an analysis and the timeframe requested by the user. The aggregation of the date will also be extracted from the date field which will be used later in the analytics functions. If you want to know more about what is in the FRED dataset well... maybe ask the FRED AI agent. ;)

## ClaudeDataPlanBuilder
This class is used to make a plan that will be sent to Claude. To make a complete dataplan for claude we need:
-question -> user input
-planner_tools -> list of tools in the planner registry
-question_intent -> the analytical intent of a user question (ranking,correlation,comparison,trend)
-series_ids -> which FRED dataset (CPIAUCSL,UNRATE,FEDFUNDS,GDP,PAYEMS)
-date_grain -> Is one of the following: 'DAY','WEEK','MONTH','QUARTER','YEAR','YEAR_MONTH' 
-start_date -> earliest date to retrieve data
-end_date -> latest date to retrieve data
-dataset_context -> metadata info about the series. sourced from metadata['title'] and the metadata['notes']

This class will call claude and ask to choose the best planner tool to build a plan based on the user conversation route. 

