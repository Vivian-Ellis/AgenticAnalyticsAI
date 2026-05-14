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
    description="""Performs full analysis""",
    input_schema={
        "type": "object",
        "properties": {
            "user_input": {
                "type": "object",
                "description": "user input question"
            }
        },
        "required": ["user_input"]
    }
)
def analytic_route(user_input,metadata=None,chat_history=None):
    agentresponse = orcestrator.run_analytics_agent(user_input)
    return {
        "summary": clean_llm_markdown(agentresponse.response['summary']),
        "chart_path": agentresponse.response['chart_path'],
        "table": agentresponse.response['table'],
        "metadata": {"route": "analytics",
                        "intent":agentresponse.response["metadata"]["intent"]}
    }


@register_conversation(
    "greeting",
    description="""a simple hello"""
)
def greeting_route(user_input=None,metadata=None,chat_history=None):
    return {
        "summary": "Hi, I'm ready to answer questions about FRED data.",
        "chart_path": None,
        "table": None,
        "metadata": {"route": "greeting",
                        "intent":None}
    }


@register_conversation(
    "metadata",
    description="""Supplies answer to metadata inquiry""",
    input_schema={
        "type": "object",
        "properties": {
            "user_input": {
                "type": "object",
                "description": "user input question"
            },
                "metadata": {
                "type": "df",
                "description": "all available datasets info"
            }
        },
        "required": ["user_input","metadata"]
    }
)
def metadata_inquiry_route(user_input, metadata, chat_history=None):
    response = orcestrator.run_general_agent(user_input, metadata, chat_history)
    return {
        "summary": clean_llm_markdown(response),
        "chart_path": None,
        "table": None,
        "metadata": {"route": "metadata",
                        "intent":None}
    }

@register_conversation(
    "other",
    description="""Support for other/out-of-scope questions""",
    input_schema={
        "type": "object",
        "properties": {
            "user_input": {
                "type": "object",
                "description": "user input question"
            },
                "metadata": {
                "type": "df",
                "description": "all available datasets info"
            }
        },
        "required": ["user_input","metadata","chat_history"]
    }
)
def other_route(user_input, metadata, chat_history):
    action=run_conversation_action(user_input,chat_history)

    if action not in ['analytics_followup','result_clarification','unsupported']:
        action='unsupported'

    if action =='unsupported':
        return {
            "summary": "Your inquiry is not supported at this time.",
            "chart_path": None,
            "table": None,
            "metadata": {"route": "other",
                            "intent":None}}
    
    if action =='analytics_followup':
        expanded_user_input=run_followup(chat_history,user_input)
        # response = orcestrator.run_general_agent(user_input, metadata, chat_history)
        return analytic_route(expanded_user_input,metadata,chat_history)
    
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
            "metadata": {"route": "other",
                            "intent":None}
        }