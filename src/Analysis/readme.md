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
