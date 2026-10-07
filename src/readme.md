**Conversation routing**

When a user submits a question, the first layer determines what kind of conversation the user is trying to have with the application. This is separate from determining which statistical analysis they ultimately want to perform.
I start with deterministic routing for requests where the intent is sufficiently obvious. I normalize the user's input and directly identify things such as greetings, questions about the source of the data, and questions about what data is available. I chose deterministic routing for these cases because there is already a known solution. There is no reason to introduce another probabilistic decision, LLM call, additional latency, or API cost to interpret something like a greeting.
If the request doesn't match one of those deterministic routes, I give Claude access to a constrained conversation tool registry. Rather than allowing Claude to decide arbitrarily what to do, I give it a defined set of conversational capabilities and have it select the appropriate one.
Those routes include a new analytical request, an explanation of a particular economic indicator, an analytical follow-up, a clarification of a previous result, a raw data query, and a general fallback for requests the application doesn't support.
I intentionally distinguish between an analytical follow-up and a result clarification. An analytical follow-up is something like, “Now do the same thing for CPI,” or “Make that monthly.” The new question depends on the previous analysis and requires another analysis to be executed. In that case, I provide the existing conversation state so that the incomplete follow-up can be expanded into a complete analytical question and then sent back through the analytical workflow.
A result clarification is different. A user might ask something like, “What does that correlation mean?” The application already has the analytical result, so it doesn't need to retrieve the data and execute the analysis again. The existing conversational context can instead be used to expand on the previous explanation.
I also have a data-query route for situations where the user isn't asking for statistical analysis at all and simply wants to retrieve actual observations from the dataset. That lets the application provide the underlying data without unnecessarily invoking an analytical workflow.
Once Claude determines the appropriate conversation tool, Claude doesn't execute the application logic itself. Python looks up the selected tool in the registry and executes the registered function. That separation between LLM decision-making and deterministic execution is a pattern I use throughout the application.

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

**DuckDB data retrieval**

Once the DataPlan has been constructed, Python uses it to build the data request.
The data loader takes the selected FRED series IDs, start and end dates, and aggregation grain and uses them to query the cleaned FRED observations stored in DuckDB.
The query filters the observations to the requested economic series and timeframe and creates the appropriate temporal grouping required by the downstream analytical workflow. I also retrieve the corresponding FRED metadata so that later layers have context about the economic indicators being analyzed.
After the data has been retrieved, I have another validation boundary before analysis. I verify that data was actually returned, that the result has the expected structure, that the required date, value, series ID, and grouping information exists, and that there are usable numerical observations.
At that point I have converted an ambiguous natural-language request into a validated, structured analytical dataset.

**Analytical tool registry**

Once the data has been successfully retrieved, the application moves into the actual analytical layer.
Python uses the analytical intent stored in the DataPlan to look up the corresponding implementation in an analytical tool registry. That registry maps the supported intents to the Python workflows for trend analysis, ranking, correlation, and statistical comparison.
Before executing the selected tool, I also validate that the selected analytical workflow is appropriate for the data that was retrieved. Different analytical methods have different data requirements.
For example, a correlation analysis requires at least two series. A comparison needs enough groups to actually perform a comparison. A trend analysis expects a single series and enough observations and variation to support the analysis.
Only after those conditions are satisfied does Python execute the registered analytical workflow.

**Routing within analytical workflows**

Some of the analytical workflows have another decision layer because a broad analytical category can contain several possible statistical procedures.
Statistical comparison is the clearest example.
A user can ask to compare two things, but “comparison” doesn't uniquely determine what statistic or statistical test should be used. A user could be asking about differences in averages, medians, or volatility.
Within the comparison workflow, I therefore expose another constrained registry of comparison methods to Claude. Claude's responsibility is to interpret what kind of comparison the user is requesting. Python then executes the corresponding statistical implementation.
For an average comparison between two groups, for example, Python performs a Welch's t-test. For more than two groups, it performs a one-way ANOVA, and if the ANOVA is significant, the workflow can perform a Tukey post-hoc comparison.
For median or nonparametric comparisons, two groups can be evaluated with a Mann–Whitney U test, while comparisons involving more than two groups can use Kruskal–Wallis.
For volatility comparisons, the Python workflow calculates measures such as variance, standard deviation, and coefficient of variation and can use Levene's test to evaluate differences in variability.
This is an important example of how I wanted to use the LLM. Claude can interpret the semantic meaning of the user's request and determine which predefined analytical capability is appropriate, but Claude is not calculating the test statistic or p-value itself. Once the analytical method has been selected, Python performs the statistical computation.

**Deterministic statistical computation**

That boundary is one of the most important parts of the architecture.
I didn't want the LLM calculating correlations, statistical tests, rankings, or trend statistics because there is no advantage to making those computations probabilistic when established deterministic implementations already exist.
The LLM can help answer the question, “What analysis is the user asking me to perform?”
Python answers the question, “What is the actual statistical result?”
That means that once the data and analytical method are fixed, the numerical computation is reproducible. It also makes the individual analytical workflows much easier to test because I can test the Python implementation independently from the LLM's interpretation of the original question.

**Analytical result validation**

Once an analytical workflow finishes, the resulting object is also validated before it is ultimately presented to the user.
There is a common set of information that I expect from an analytical result, along with additional requirements specific to the analytical method.
For example, a correlation result needs the calculated correlation output and information about the selected correlation method. A comparison result needs the descriptive statistics, comparison type, selected statistical test, inferential results, and significance threshold.
This creates another boundary between execution and presentation so that downstream components aren't expected to work with incomplete analytical results.

**Visualization**

The analytical tools also define an appropriate default visualization.
Once the analysis has been completed, the application can use the chart type registered with that analytical workflow to generate a visualization of the result.
That means the application isn't limited to returning an LLM response. The user can receive the natural-language interpretation along with the underlying analytical output and an appropriate visualization.

**LLM narration**

The final responsibility of the LLM is narration.

Once Python has produced the statistical results, I provide those calculated outputs and the relevant dataset context to Claude. At this stage, Claude's job is not to perform the statistical analysis again. Its responsibility is to translate the computed results into a natural-language explanation that is useful to the user.

This gives me a final separation of responsibilities:
Claude interprets and orchestrates where semantic reasoning is valuable. Python retrieves the data and performs the statistical computation. Claude then narrates the resulting statistics.
The final response can then be returned to the application with the statistical output, table, and visualization.
