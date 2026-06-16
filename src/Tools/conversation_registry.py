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
    description="""Use for new FRED questions that require computation or interpretation, including:
comparisons, trends, rankings, correlations, charts, statistical summaries, or higher/lower questions.
Examples: compare inflation in 2024 vs 2025; top 5 unemployment months; when did inflation accelerate?""",
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

# #what datasets we have --------------------------------
# @register_conversation(
#     "available_data",
#     description="""Use this when the user asks about available FRED datasets.""",
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
def available_data_inquiry_route(user_input,session_state=None):
    fred_metadata = session_state.fred_metadata[["series_id","title","frequency","seasonal_adjustment","observation_start","observation_end"]]
    return {
        "summary": "**Available FRED datasets**",
        "chart_path": None,
        "table": fred_metadata,
        "data_plan": {"route": "available_data", "intent": None}
    }

# # clarify what the series means---------------------------------
# @register_conversation(
#     "explain_series",
#     description="""Use when the user asks what a specific FRED series, series ID, dataset, or economic indicator means.""",
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
# def explain_series_route(user_input,session_state=None):
#     top_results=[]
#     inferred_series_intent = run_series_intent_prompt(user_input)
#     top_results.extend(inferred_series_intent.split(','))
#     print(top_results)
#     fred_metadata = session_state.fred_metadata
#     fred_metadata=fred_metadata[fred_metadata['series_id'].isin(top_results)]

#     message=f"**{fred_metadata['updated_title'].iloc[0]}**\n\n{fred_metadata['description'].iloc[0]}"
#     return {
#         "summary": message,
#         "chart_path": None,
#         "table": None,
#         "data_plan": {"route": "explain_series",
#                         "intent":None}
#     }

# # --- ANALYTICS FOLLOWUP: rerun/modify prior analysis && RESULT CLARIFICATION: explain prior result, no rerun---
# @register_conversation(
#     "followup",
#     description="""Use when the user refers to a previous analysis or result, either to modify/rerun it or to ask for clarification, explanation, or interpretation.""",
#     input_schema={
#         "type": "object",
#         "properties": {"user_input": {"type": "string"}},
#         "required": ["user_input"]
#     }
# )
# def followup_route(user_input, session_state=None):
#     return {
#         "summary": "underconstruction",
#         "chart_path": None,
#         "table": None,
#         "data_plan": {"route": "followup",
#                         "intent":None}
#     }

# --- ANALYTICS FOLLOWUP: rerun/modify prior analysis ---
@register_conversation(
    "analytics_followup",
    description="Rerun or MODIFY the previous analysis, reusing prior context "
                "(analysis type, ranking, timeframe, grouping, series). "
                "E.g. 'now do CPI', 'make it monthly', 'top 10 instead', 'what about unemployment'.",
    input_schema={
        "type": "object",
        "properties": {"user_input": {"type": "string"}},
        "required": ["user_input"]
    }
)
def analytics_followup_route(user_input, session_state=None):
    chat_history = session_state.get("messages", []) if session_state else []
    expanded_user_input=run_followup(chat_history,user_input)
    return analytic_route(expanded_user_input) #TO-DO make sure to save the enriched user input not the raw input

# --- RESULT CLARIFICATION: explain prior result, no rerun ---
@register_conversation(
    "result_clarification",
    description="Explain, interpret, or summarize a PREVIOUS result WITHOUT rerunning it. "
                "E.g. 'what does this mean?', 'explain this correlation', 'why use spearman?'.",
    input_schema={
        "type": "object",
        "properties": {"user_input": {"type": "string"}},
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

# # --- DATA SOURCE: provenance ---
# @register_conversation(
#     "data_source",
#     description="User asks where the FRED data comes from / its origin or source.",
#     input_schema={
#         "type": "object",
#         "properties": {"user_input": {"type": "string"}},
#         "required": ["user_input"]
#     }
# )
def data_source_route(user_input,session_state=None):
    message="""The data used in this AI agent comes from the Federal Reserve Economic Data (FRED) API, provided by the Federal Reserve Bank of St. Louis.

API docs: https://fred.stlouisfed.org/docs/api/fred/overview.html"""
    
    return {
        "summary": message,
        "chart_path": None,
        "table": None,
        "data_plan": {"route": "data_source",
                        "intent":None}}

#show data in the database-------------------------
@register_conversation(
    "data_query",
    description="Return actual data VALUES in a table: latest/current value, values by year/month/quarter, or filtered/grouped rows (where, group by). Use for raw observations, NOT for computed analysis.",
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
def data_query_route(user_input,session_state=None):
    df=orcestrator.run_query_agent(user_input)
    return {
        "summary": "",
        "chart_path": None,
        "table": df,
        "data_plan": {"route": "data_query",
                        "intent":None}}

#not supported --------------------------
@register_conversation(
    "general",
description="Fallback for requests that are out of scope, unrelated to FRED data, or too ambiguous to route. Use only when no other tool fits.",    
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
def general_route(user_input,session_state=None):
    message="Your inquiry is not supported at this time."

    return {
        "summary": message,
        "chart_path": None,
        "table": None,
        "data_plan": {"route": "general",
                        "intent":None}}
