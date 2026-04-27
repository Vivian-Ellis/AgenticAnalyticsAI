RANKING_SEMANTICS = {
"UNRATE": {
    "higher_interpretation": "worse unemployment",
    "lower_interpretation": "better unemployment"
},
"CPIAUCSL": {
    "higher_interpretation": "higher prices/inflation level",
    "lower_interpretation": "lower prices/inflation level"
},
"FEDFUNDS": {
    "higher_interpretation": "higher interest rate",
    "lower_interpretation": "lower interest rate"
},
"GDP": {
    "higher_interpretation": "higher output/economic activity",
    "lower_interpretation": "lower output/economic activity"
},
"PAYEMS": {
    "higher_interpretation": "higher payroll employment",
    "lower_interpretation": "lower payroll employment"
}
}

def dataset_ranking_semantics(series_ids):
    # ranking parameters
    ranking_semantics_str=""

    for series in series_ids:
        ranking_semantics_str+=f"{series}:\n"
        for key,value in RANKING_SEMANTICS[series].items():
            ranking_semantics_str+=f"\t- {key} means {value}\n"

    return ranking_semantics_str