import anthropic

client = anthropic.Anthropic()

import duckdb
import pandas as pd

def table_summary():
    con = duckdb.connect("raw_data.db")

    df=con.execute("SELECT * FROM raw_fred_data").fetchdf()
    descriptive_statistics=df.describe()
    return df,descriptive_statistics

def summarize_analysis(question, results_preview, key_stats):
    message = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=100,
                messages=[
                    {
                        "role": "user",
                        "content": f"{question} {key_stats} {results_preview}"
                    }
                    ],
            )
    print(message.content)
    # print(message)

import os
print(os.getenv("ANTHROPIC_API_KEY"))

df,descriptive_statistics=table_summary()
summarize_analysis("please give me 1 short executive summary of the dataset given, 3 bullet insights, and  1 caution/limitation of the provided dataset.", df, descriptive_statistics)