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

**Constructing the analytical DataPlan**

If the conversation is routed to analytics, the next objective is to convert the natural-language request into a structured DataPlan that contains the information the deterministic analytical layer will need.
The plan defines the analytical intent, the FRED series IDs, the date aggregation grain, the start and end dates, and dataset context.
There is another constrained tool-selection layer at this stage. Claude selects the appropriate planning capability, and Python executes the registered planning function. The planner then determines the individual components required to construct the complete DataPlan.
The first component is the analytical intent—whether the user is asking for a trend, ranking, correlation, or comparison.
For this problem, I didn't think an LLM was necessary for every request because analytical intent is a relatively bounded classification problem. I therefore use a hybrid classification approach.
I first use deterministic rule-based overrides for questions with strong lexical signals. For example, terms such as “top,” “bottom,” “highest,” and “lowest” strongly indicate a ranking request. Terms such as “correlation,” “relationship,” or “move together” indicate correlation. Terms such as “compare,” “difference,” “before,” or “after” indicate a comparison.
If none of those deterministic rules identify the intent, I fall back to a pretrained logistic-regression classifier that predicts the analytical category.
That gives me another opportunity to avoid an LLM call. Rather than asking a much larger language model to solve a small bounded classification problem every time, I can use deterministic rules where possible and a lightweight supervised model for the remaining cases.

**FRED series selection**

Once I understand what kind of analysis the user wants, I need to determine which economic series the question refers to.
This is an area where I deliberately use Claude because economic indicators can have overlapping semantics and users aren't necessarily going to refer to them using their exact FRED series IDs.
For example, a user may ask about inflation, employment, prices, or interest rates without knowing the exact underlying series. That becomes a semantic interpretation problem rather than a simple deterministic lookup.
Claude interprets the natural-language question and identifies the relevant FRED series IDs. I can then retrieve the corresponding metadata for those series and construct dataset context that can be used later in the analytical and narration layers.

**Temporal interpretation**

The DataPlan also needs to determine the appropriate aggregation grain and timeframe.
For the aggregation grain, Claude interprets whether the user is asking for the data by day, week, month, quarter, year, or year-month. That output is then checked against a constrained set of values that the downstream application supports.
I also use Claude to interpret the requested date range because users can express time in many different ways. They may specify explicit dates, but they can also say things such as “over the last five years,” “since 2020,” or “before and after 2022.”
The date-range prompt has access to the latest observation date available in my FRED metadata so that relative time expressions can be resolved against the data that is actually available.
This is also one of the places where I explicitly enforce a deterministic validation boundary around an LLM output.
Python expects the LLM's date-range output to satisfy a particular contract. If the returned value doesn't satisfy the required date format, I don't allow that malformed output to continue through the pipeline. Instead, I trigger a constrained retry prompt that includes the previous invalid response, the original question, and the exact format required:
YYYY-MM-DD,YYYY-MM-DD
Python then validates the retry again. If a usable date range still cannot be generated, I have a deterministic fallback rather than allowing an invalid LLM output to propagate into the database query.
The broader design principle is that whenever information moves from the probabilistic LLM layer into deterministic application code, I try to define and enforce a predictable interface between the two.

**DataPlan validation**

Once all of those components have been assembled, I validate the DataPlan before allowing it to reach the data-retrieval and analytical layers.
The validation checks things such as whether the analytical intent is supported, whether at least one series was identified, whether the series IDs have the expected representation, whether the requested aggregation grain is supported, whether both dates exist, and whether the start date occurs before the end date.
The purpose is to catch an invalid analytical plan as early as possible rather than allowing an upstream problem to propagate through the rest of the system.
