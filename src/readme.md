





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
