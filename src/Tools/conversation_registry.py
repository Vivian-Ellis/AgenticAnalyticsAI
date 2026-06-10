from Tools.registries.conversation_tool_registry import register_conversation
from Orcestrator import orcestrator
from pathlib import Path
from dotenv import load_dotenv
import sys
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.append(str(SRC_DIR))

env_path = PROJECT_ROOT / ".env"
load_dotenv(env_path, override=True)

from Orcestrator.conversationstatehelper import clean_llm_markdown
from Narration.summaries import run_conversation_action,run_followup,run_clarification_prompt,run_metadata_assistant,run_series_intent_prompt
from DataBase.db import get_table_preview

#main analytics route---------------------
@register_conversation(
    "analytics",
    description="""Use this when the user is asking for a data analysis, statistical analysis, 
    ranking, comparison, correlation, trend analysis, time-based analysis, chart, or 
    quantitative answer using FRED economic data.""",
    input_schema={
        "type": "object",
        "properties": {
            "user_input": {
                "type": "string",
                "description": "The user's most recent message or analytical question."
            }
        },
        "required": ["user_input"]
    }
)
def analytic_route(user_input,session_state=None):
    agentresponse = orcestrator.run_analytics_agent(user_input)
    return {
        "summary": clean_llm_markdown(agentresponse.response['summary']),
        "chart_path": agentresponse.response['chart_path'],
        "table": agentresponse.response['table'],
        "data_plan": {"route": "analytics",
                        "intent":agentresponse.response["data_plan"]["intent"]}
    }

#simple greeting -----------------------
@register_conversation(
    "greeting",
    description="""Use this for simple greetings like hi, hello, hey, or when the user is casually starting the chat.""",
    input_schema={
        "type": "object",
        "properties": {},
        "required": []
    }
)
def greeting_route(session_state=None):
    return {
        "summary": "Hi, I'm ready to answer questions about FRED data.",
        "chart_path": None,
        "table": None,
        "data_plan": {"route": "greeting",
                        "intent":None}
    }

#what datasets we have --------------------------------
@register_conversation(
    "available_data",
    description="""Use this when the user asks about available FRED datasets.""",
    input_schema={
        "type": "object",
        "properties": {
            "user_input": {
                "type": "string",
                "description": "The user's most recent metadata or dataset availability question."
            }
        },
        "required": ["user_input"]
    }
)
def available_data_inquiry_route(user_input,session_state=None):
    fred_metadata = session_state.fred_metadata[["series_id","title","frequency","seasonal_adjustment","observation_start","observation_end"]]
    return {
        "summary": "**Available FRED datasets**",
        "chart_path": None,
        "table": fred_metadata,
        "data_plan": {"route": "available_data", "intent": None}
    }

# clarify what the series means---------------------------------
@register_conversation(
    "explain_series",
    description="""Use when the user asks what a specific FRED series, series ID, dataset, or economic indicator means.""",
    input_schema={
        "type": "object",
        "properties": {
            "user_input": {
                "type": "string",
                "description": "The user's most recent metadata or dataset availability question."
            }
        },
        "required": ["user_input"]
    }
)
def explain_series_route(user_input,session_state=None):
    top_results=[]
    inferred_series_intent = run_series_intent_prompt(user_input)
    top_results.extend(inferred_series_intent.split(','))
    print(top_results)
    fred_metadata = session_state.fred_metadata
    fred_metadata=fred_metadata[fred_metadata['series_id'].isin(top_results)]

    message=f"**{fred_metadata['updated_title'].iloc[0]}**\n\n{fred_metadata['description'].iloc[0]}"
    return {
        "summary": message,
        "chart_path": None,
        "table": None,
        "data_plan": {"route": "explain_series",
                        "intent":None}
    }

# #all other metadata inquiries ----------------------------------
# @register_conversation(
#     "metadata_inquiry",
#     description="""Use for metadata questions not covered by available_data or explain_series.
#     This includes questions about units, frequency, seasonal adjustment, observation ranges, metadata fields,
#     or comparisons of metadata across available FRED series.""",
#     input_schema={
#         "type": "object",
#         "properties": {
#             "user_input": {
#                 "type": "string",
#                 "description": "The user's most recent metadata or dataset availability question."
#             }
#         },
#         "required": ["user_input"]
#     }
# )
# def metadata_inquiry_route(user_input,session_state=None):
#     fred_metadata = session_state.fred_metadata.to_markdown(index=False)
#     response = run_metadata_assistant(user_input, fred_metadata)
#     return {
#         "summary": clean_llm_markdown(response),
#         "chart_path": None,
#         "table": None,
#         "data_plan": {"route": "metadata_inquiry",
#                         "intent":None}
#     }

#follow up from previous Q ----------------------------
@register_conversation(
    "analytics_followup",
    description="""The user wants to rerun or modify a previous analytics workflow while preserving prior analytical context such as analysis type, ranking structure, timeframe, grouping, or compared series.
    for examples now do CPI,what about unemployment,make it monthly,top 10 instead, use GDP""",
    input_schema={
        "type": "object",
        "properties": {
            "user_input": {
                "type": "string",
                "description": "The user's most recent message."
            }
        },
        "required": ["user_input"]
    }
)
def analytics_followup_route(user_input, session_state=None):
    chat_history = session_state.get("messages", []) if session_state else []
    expanded_user_input=run_followup(chat_history,user_input)
    return analytic_route(expanded_user_input) #TO-DO make sure to save the enriched user input not the raw input

#clarify the previous chat bot response -------------------
@register_conversation(
    "result_clarification",
    description="""The user wants explanation, interpretation, clarification, expansion, or summarization of a previous analytical result without rerunning the workflow.
    - examples: explain this correlation, what does this mean?, summarize the chart, why was spearman used?""",
    input_schema={
        "type": "object",
        "properties": {
            "user_input": {
                "type": "string",
                "description": "The user's most recent message."
            }
        },
        "required": ["user_input"]
    }
)
def result_clarification_route(user_input,session_state=None):
    chat_history = session_state.get("messages", []) if session_state else []
    analysis_response=chat_history #TO-DO fix use methodology in state
    message=run_clarification_prompt(chat_history=chat_history,
                                analysis_response=analysis_response,
                                clarification_question=user_input)
    return {
        "summary": clean_llm_markdown(message),
        "chart_path": None,
        "table": None,
        "data_plan": {"route": "result_clarification",
                        "intent":None}
    }

##new route
# note: FRED is a free, publicly accessible data for research --------------------------
@register_conversation(
    "data_source",
    description="""the user wants to know where the FRED data that is being used originates from.""",
    input_schema={
        "type": "object",
        "properties": {
            "user_input": {
                "type": "string",
                "description": "The user's most recent message."
            }
        },
        "required": ["user_input"]
    }
)
def data_source_route(user_input,session_state=None):
    message="""The data used in this AI agent comes from the Federal Reserve Economic Data (FRED) API, provided by the Federal Reserve Bank of St. Louis.

API docs: https://fred.stlouisfed.org/docs/api/fred/overview.html"""
    
    return {
        "summary": message,
        "chart_path": None,
        "table": None,
        "data_plan": {"route": "data_source",
                        "intent":None}}


#new route that will show a preview of the data in the database-------------------------
@register_conversation(
    "data_preview",
    description="""user wants to see a preview of the data available in the database. The user wants to view actual rows from the database/dataset.

Call this when the user asks to:
- show a sample of the data
- show example data
- preview the data
- show the first rows
- show the table structure
- inspect columns
- see what the dataset looks like

this will provide the first 5 rows of the requests dataset for the user to quickly inspect the structure, column names, and data types of the data.""",
    input_schema={
        "type": "object",
        "properties": {
            "user_input": {
                "type": "string",
                "description": "The user's most recent message."
            }
        },
        "required": ["user_input"]
    }
)
def data_preview_route(user_input,session_state=None):
    top_results=[]
    inferred_series_intent = run_series_intent_prompt(user_input)
    top_results.extend(inferred_series_intent.split(','))
    print(top_results)
    # fred_metadata = session_state.fred_metadata
    # fred_metadata=fred_metadata[fred_metadata['series_id'].isin(top_results)]

    preview_df=get_table_preview(series_ids=top_results)
    return {
        "summary": "",
        "chart_path": None,
        "table": preview_df,
        "data_plan": {"route": "data_preview",
                        "intent":None}}


#not supported --------------------------
@register_conversation(
    "unsupported",
    description="""user is truly out of scope, unrelated, ambiguous, or cannot reasonably reference prior analytical context.""",
    input_schema={
        "type": "object",
        "properties": {
            "user_input": {
                "type": "string",
                "description": "The user's most recent message."
            }
        },
        "required": ["user_input"]
    }
)
def unsupported_route(user_input,session_state=None):
    return {
        "summary": "Your inquiry is not supported at this time.",
        "chart_path": None,
        "table": None,
        "data_plan": {"route": "unsupported",
                        "intent":None}}

# #bot help for beginners who dont know how to use --------------------------
# @register_conversation(
#     "assistance_needed",
#     description="""the user does not know how to use the ai agent and wants suggestions on what type of wuestions can be asked and the capabilities that the bot is capable of.""",
#     input_schema={
#         "type": "object",
#         "properties": {
#             "user_input": {
#                 "type": "string",
#                 "description": "The user's most recent message."
#             }
#         },
#         "required": ["user_input"]
#     }
# )
# def assistance_needed_route(user_input,session_state=None):
#     message = """
#     I provide statistical analysis of Federal Reserve Economic Data (FRED).

#     Examples:
#     - Top 5 unemployment years
#     - Was inflation higher in 2022 than 2018?
#     - Is there a relationship between interest rates and unemployment?

#     I can also help explain available datasets and metadata.

#     Follow-up questions are supported:
#     - Now do GDP
#     - Make it monthly
#     - Top 10 instead
#     - Why was that test used?"""

#     return {
#         "summary": message,
#         "chart_path": None,
#         "table": None,
#         "data_plan": {"route": "assistance_needed",
#                         "intent":None}}
