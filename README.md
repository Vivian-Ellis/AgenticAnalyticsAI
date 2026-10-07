# AgenticAnalyticsAI
This is a FRED analytics agent meant to answer questions about Federal Reserve Economic Data (FRED). 

The main purpose of this AI agent is to summarize analytical questions about FRED but is also capable of answering quetions about metadata, data retrevial, follow-up requests, methodology clarification.

**📊 Analytical Questions**
The current implemented analytical capabilities are trend analysis, rankings, comparisons, correlations, and statistical relationships across economic indicators. Examples:
- How has payroll employment changed over time?
- What were the lowest GDP quarters in the past 10 years?
- Compare employment levels before and after COVID.
- How strongly are GDP and employment correlated?

**📚 Metadata & Definitions**
You can ask about the source of the data at anytime. Examples:
- What datasets are available?
- What does CPI mean?
- What is the source of this data?

**🔄 Follow-Up Requests**
You can ask follow-up questions at any time, and I'll use the context of our conversation to refine or extend the analysis. Examples of follow-ups:
- Now do GDP.
- Make it monthly.
- Bottom 6 instead.
- Compare that to unemployment.

**💡 Methodology & Clarifications**
After the agent performs the analysis you are able to ask clarifications on how the FRED agent arrived at an analysis. Examples:
- Why did you use Spearman correlation?
- Explain the p-value.
- How was this comparison performed?

## FRED Agentic Analytics — Full Project Explanation
I decided that I wanted to build an agentic analytics application that would allow users to ask natural-language questions about economic data and receive an actual statistical analysis rather than having an LLM generate the statistics itself.

I chose economic data because it is publicly accessible, relatively straightforward to integrate, and gave me a controlled domain where I could focus on designing the agentic architecture. I used FRED as the underlying economic data source and DuckDB as a lightweight analytical database for storing and querying the cleaned observations and metadata.

Rather than trying to build a completely general-purpose data analyst, I intentionally constrained the initial scope. I defined four primary analytical workflows that the application would support: trend analysis, ranking, correlation, and statistical comparison. That gave me a bounded set of analytical capabilities that I could implement, validate, and test in Python.

The main architectural principle I established was to separate interpretation from computation. I use Claude where natural-language interpretation, semantic reasoning, or decision-making under ambiguity is useful, while Python performs the actual statistical computation. After Python completes the analysis, Claude is used again as a narration layer to translate those calculated results into a natural-language explanation.

I also deliberately designed the application as a hybrid architecture rather than routing every decision through an LLM. My general principle was that if I already had a deterministic and reliable solution to a problem, I didn't want to introduce the additional latency, API cost, and nondeterminism of another LLM call. I wanted to reserve the LLM for situations where its ability to interpret natural language or resolve ambiguity actually added value.

## Overall architecture
At a high level, the complete workflow is:

Natural-language question → deterministic conversation routing where possible → constrained Claude conversation routing where necessary → Python executes the selected route → analytical DataPlan construction → rule-based + logistic-regression analytical intent classification → Claude FRED series and temporal interpretation → deterministic validation and constrained retries → DataPlan validation → DuckDB data retrieval → retrieved-data validation → analytical tool selection → tool/data compatibility validation → Python statistical workflow → additional constrained routing where an analytical workflow requires it → deterministic statistical computation → result validation → visualization → constrained LLM narration → response to the user.

The principle I tried to apply throughout the project was to use the least complex reliable method for each problem.

I don't use an LLM simply because an LLM is available. If deterministic code can reliably solve the problem, I use deterministic code. If a small supervised model can solve a bounded classification problem, I can use that instead of an LLM. I reserve the LLM for the areas where language understanding, semantic ambiguity, or dynamic decision-making actually require it.

That allowed me to build the application as a hybrid system where the LLM provides flexibility and natural-language reasoning without making the entire analytical pipeline probabilistic. The statistical computation remains reproducible, and I reduce unnecessary LLM calls that would otherwise add latency and API cost.
