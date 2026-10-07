







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
