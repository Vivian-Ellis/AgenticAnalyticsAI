from Tools.registries.conversation_tool_registry import register_conversation
from Orcestrator import orcestrator
from pathlib import Path
from dotenv import load_dotenv
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.append(str(SRC_DIR))

env_path = PROJECT_ROOT / ".env"
load_dotenv(env_path, override=True)

from Orcestrator.conversationstatehelper import clean_llm_markdown
from Narration.summaries import run_conversation_action,run_followup

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
def analytic_route(user_input):
    agentresponse = orcestrator.run_analytics_agent(user_input)
    return {
        "summary": clean_llm_markdown(agentresponse.response['summary']),
        "chart_path": agentresponse.response['chart_path'],
        "table": agentresponse.response['table'],
        "data_plan": {"route": "analytics",
                        "intent":agentresponse.response["data_plan"]["intent"]}
    }

@register_conversation(
    "greeting",
    description="""Use this for simple greetings like hi, hello, hey, or when the user is casually starting the chat.""",
    input_schema={
        "type": "object",
        "properties": {},
        "required": []
    }
)
def greeting_route():
    return {
        "summary": "Hi, I'm ready to answer questions about FRED data.",
        "chart_path": None,
        "table": None,
        "data_plan": {"route": "greeting",
                        "intent":None}
    }


@register_conversation(
    "metadata_inquiry",
    description="""Use this when the user asks about available FRED datasets, dataset names, series IDs,
    date ranges, frequencies, units, metadata, or examples of questions the app can answer.""",
    input_schema={
        "type": "object",
        "properties": {
            "user_input": {
                "type": "string",
                "description": "The user's most recent metadata or dataset availability question."
            },
            "fred_metadata": {
                "type": "string",
                "description": "Markdown table containing available FRED dataset metadata."
            },
            "chat_history": {
                "type": "array",
                "description": "Recent chat history as a list of message dictionaries.",
                "items": {
                    "type": "object"
                }
            }
        },
        "required": ["user_input", "fred_metadata"]
    }
)
def metadata_inquiry_route(user_input, fred_metadata, chat_history=None):
    response = orcestrator.run_general_agent(user_input, fred_metadata, chat_history)
    return {
        "summary": clean_llm_markdown(response),
        "chart_path": None,
        "table": None,
        "data_plan": {"route": "metadata_inquiry",
                        "intent":None}
    }

@register_conversation(
    "other",
    description="""Use this for unsupported, unrelated, ambiguous, or general app questions that are not clearly
    FRED analytics, FRED metadata, or a greeting. This can also inspect follow-up behavior using chat history.""",
    input_schema={
        "type": "object",
        "properties": {
            "user_input": {
                "type": "string",
                "description": "The user's most recent message."
            },
            "fred_metadata": {
                "type": "string",
                "description": "Markdown table containing available FRED dataset metadata."
            },
            "chat_history": {
                "type": "array",
                "description": "Recent chat history as a list of message dictionaries.",
                "items": {
                    "type": "object"
                }
            }
        },
        "required": ["user_input", "fred_metadata", "chat_history"]
    }
)
def other_route(user_input, fred_metadata, chat_history):
    action=run_conversation_action(user_input,chat_history)

    if action not in ['analytics_followup','result_clarification','unsupported']:
        action='unsupported'

    if action =='unsupported':
        return {
            "summary": "Your inquiry is not supported at this time.",
            "chart_path": None,
            "table": None,
            "data_plan": {"route": "other",
                            "intent":None}}
    
    if action =='analytics_followup':
        expanded_user_input=run_followup(chat_history,user_input)
        # response = orcestrator.run_general_agent(user_input, metadata, chat_history)
        return analytic_route(expanded_user_input)
    
    if action =='result_clarification':
        # expanded_user_input=run_followup(chat_history,user_input)
        # # response = orcestrator.run_general_agent(user_input, metadata, chat_history)
        # response=analytic_route(expanded_user_input,metadata,chat_history)
        print(chat_history)
        print("--------------------------")
        print(len(chat_history))
        return {
            "summary": "Thinking...",
            "chart_path": None,
            "table": None,
            "data_plan": {"route": "other",
                            "intent":None}
        }