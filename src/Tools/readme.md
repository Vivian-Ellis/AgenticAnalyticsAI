# Tools Registry
The `Tools` folder contains the tool registry for 4 main components of the FRED AI agent:
- analytical tools
- charting tools
- conversation tools
- planner tools

There are two files associated for each resgistry: a tool_registry.py script which contains the class needed to register tools, get tools by name, and list out all the available tools. There is also the registry.py which registers functions as tool the the associated class.

## Analytics Registry
There are 4 tools registered in analytics that help claude determine the analytical methodology needed based on the users input.

There is a `ranking` tool which performs ranking analysis by interpreting the semantic intent of a ranking question, determining the appropriate ranking direction and number of results, aggregating the dataset, and ranking grouped periods by the calculated metric. Generates a narrated summary of the ranked results and returns a structured `RankingResult` object containing the rankings, metadata, and analysis outputs.

There is a `correlation` tool which performs correlation analysis by reshaping and aggregating time series data, testing for outliers and normality, and dynamically selecting either Pearson or Spearman correlation based on the statistical properties of the data. Generates a narrated interpretation of the correlation results

There is a `comparison` tool which performs statistical comparison analysis for questions that compare values across groups, periods, or event-defined cohorts.
It will be used for questions asking whether one group, period, or cohort is higher, lower, greater, smaller, more, less, different, more stable, more volatile, or otherwise different from another. The comparison analysis delegates to specialized comparison tools such as average_comparison, median_comparison, and volatility_comparison, then selects the appropriate statistical test based on the number of groups and comparison type. Examples include Welch’s t-test, one-way ANOVA, Mann-Whitney U, Kruskal-Wallis, and Levene’s test.

There is a `trend` tool which performs TBD

:point_up::thread: Remember analytics is the _intent_

## Charts Registry
The chart registry has 3 main charts used by FRED AI agent: Bar plot, Scatter plot, and a Timeseries plot. These charts use bokeh for interactive abilities. Charts are associated to the particular analysis type for the given user question. This makes sure that only the appropriate charts are used for each analysis types:
- Ranking analysis -> Bar chart
- Comparison analysis -> Bar chart
- Correlation analysis -> Scatter plot
- Trend analysis -> Timeseries plot

The chart registry does not currently have the ability to take requests from users on what charts to use. Charts will always print to the chat log when available.

## Conversation Registry 
The conversaion registry help claude determine the route. A route is definded by the type of quesiton a user intends on: 
-analytics, this will produce a full analytical summary.
-greeting, this is used for simple greetings like hi, hello, hey, or when the user is casually starting the chat.
-metadata_inquiry, this is used to provide information about available FRED datasets, dataset names, series IDs, date ranges, frequencies, units, metadata, or examples of questions the app can answer.
-analytics_followup, a follow up to a previously asked analytical question
-result_clarification, the user wants clarification on a previous analytical summary.
unsupported, a catch all for unsupported questions used when the question is truly out of scope, unrelated, ambiguous, or cannot reasonably reference prior analytical context.

:point_up::thread: Remember conversation is the _route_

## Planner Registry
The planner registry helps claude to build the data plan needed to run an analysis. The data plan build is found here `src/plan/DataPipeline.ClaudeDataPlanBuilder`.

A data plan needs the following:
-question
-planner_tools
-question_intent
-series_ids
-date_grain
-start_date
-end_date
-dataset_context
More about these parameters can be found in the DataPipeline readme.md

The registered planner tools are:

-predict_analytical_intent -> this tool will predict the analytical intent of the question. The following categories are options: ["trend","comparison","ranking", "correlation","unsupported"]
-predict_series_intent -> this tool will select the best FRED series IDs for the user question using an LLM prompt to determine which dataset to perform and analysis on. Prompt can be found here prompts/
-timeline_intent -> this tool uses claude LLM to determine a date range for the user question. this function also performs validation of the LLM results and if validation fails the LLM will attempt to extract the date again. If the LLM cannot find a vlaid date we will use "2016-01-01" thru last time FRED data was updated. Prompt can be found here prompts/
-date_aggregation_grain_intent -> this tool uses claude LLM to determine the best date grain (aggresgation on the date field) for the users question. Is one of the following: 'DAY','WEEK','MONTH','QUARTER','YEAR','YEAR_MONTH'. Prompt can be found here prompts/ 
-build_entire_data_plan -> Builds the complete DataPlan for an analytical FRED question. This is used for when the user asks a new analytical question.

All tools (besides build_entire_data_plan) can be used to modify an existing data plan so that we do not have to rebuild the data plan when the route is `analytics_followup`