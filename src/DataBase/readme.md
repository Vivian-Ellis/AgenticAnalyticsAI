**DuckDB data retrieval**

Once the DataPlan has been constructed, Python uses it to build the data request.
The data loader takes the selected FRED series IDs, start and end dates, and aggregation grain and uses them to query the cleaned FRED observations stored in DuckDB.
The query filters the observations to the requested economic series and timeframe and creates the appropriate temporal grouping required by the downstream analytical workflow. I also retrieve the corresponding FRED metadata so that later layers have context about the economic indicators being analyzed.
After the data has been retrieved, I have another validation boundary before analysis. I verify that data was actually returned, that the result has the expected structure, that the required date, value, series ID, and grouping information exists, and that there are usable numerical observations.
At that point I have converted an ambiguous natural-language request into a validated, structured analytical dataset.
