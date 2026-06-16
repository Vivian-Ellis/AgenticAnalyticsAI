from pathlib import Path
from dotenv import load_dotenv
import sys
sys.path.append("../src/")
import json

from Tools.registries.conversation_tool_registry import list_anthropic_conversation_tools,get_conversation_tool
from Tools import conversation_registry #need to import this because it populates the resigstry with all the tools in the script
from Narration import summaries

from datetime import datetime
import time
import re

PROJECT_ROOT = Path(__file__).resolve().parents[2]

with open(PROJECT_ROOT / "data" / "date_labels.json", "r") as f:
    DATE_LABELS = json.load(f)

SRC_DIR = PROJECT_ROOT / "src"
sys.path.append(str(SRC_DIR))

env_path = PROJECT_ROOT / ".env"
load_dotenv(env_path, override=True)

CONVERSATION_TOOLS = list_anthropic_conversation_tools()

GREETINGS = {"hi","hello","hey","howdy","sup","yo","hiya","greetings",
                "morning","afternoon","evening","whats up","what's up"}

DATA_SOURCE_PHRASES = {
    "what does fred mean", "what does fred stand for","what is fred","link to the fred api","fred api",
    "fred api docs", "where was this data pulled","where was this data sourced", "where was the data pulled",
    "where was the data sourced", "where does the data come from","where is the data from","what is the data source", 
    "what's the data source","what is the source", "what's the source","source of the data","is this from fred","is this fred data"}

AVAILABLE_DATA_PHRASES = {
    "what data do you have","what datasets do you have","what fred data do you have","what fred datasets do you have",
    "available data","available datasets","show available data","show available datasets","list datasets","list available datasets"}

def normalize_input_text(text):
    text = text.lower().strip()      # lowercase + trim ends
    text = re.sub(r"[?!.]+$", "", text)  # remove ending punctuation
    text = re.sub(r"\s+", " ", text)     # collapse whitespace
    return text

def date_cleanup(table):
    for grain in ["WEEK", "MONTH", "QUARTER"]:
        if grain in table.columns:
            table[grain] = (
                table[grain]
                .astype(str)
                .map(DATE_LABELS[grain]))

def markdown_table_helper(table,analysis_type):
    #for rank
    if table is not None:
        if analysis_type=="ranking":
            table = table.copy()
            table.index = table.index + 1
            table.index.name = "Rank"
            # human readable dates
            date_cleanup(table)
            # format header
            table.columns = [col.replace("_", " ").title() for col in table.columns]
            #round values
            table["Value"] = table["Value"].round(2)
            # display table to chat
            return table
        else:
            return table

def clean_llm_markdown(text: str) -> str:
    if text is None:
        return ""
    text = str(text)
    # remove accidental Python repr wrapping
    if text.startswith("'") and text.endswith("'"):
        text = text[1:-1]
    # convert escaped newlines if model output came through as a repr string
    text = text.replace("\\n", "\n")
    # escape Markdown math delimiters caused by currency
    text = text.replace("$", r"\$")
    # optional: normalize weird bullets
    text = text.replace("•", "-")
    return text

#question route is NOT the analytical intent , this instead is the conversation route: 
# analytics-user wants to perform some analytical task
# greeting-user is just saying hi
# other -this type of user input is not currently supported
def question_routing(user_input, session_state=None):
    chat_history = session_state.get("messages", []) if session_state else []
    message = f"""select exactly one tool, do not explain.
    User:
    {user_input}
    """
#     message = f"""You are a routing layer. You must call exactly one conversation tool.

# Do not answer the user directly.
# Do not ask clarifying questions.
# If the message is asking for any FRED data analysis, call analytics.

# Examples:
# - "bottom 7 unrate months in 2019" -> analytics
# - "top 5 CPI years" -> analytics
# - "now for CPI" -> analytics_followup
# - "what datasets can I use?" -> metadata_inquiry
# - "hi" -> greeting

# Recent chat history:
# {chat_history}

# User message:
# {user_input}"""
    #determanistic routing first
    user_input_text=normalize_input_text(user_input)
    if user_input_text in GREETINGS: #general greetings
        result = {"summary":  "Hi, I'm ready to answer questions about FRED data.",
                    "chart_path": None,
                    "table": None,
                    "data_plan": {"route": "general",
                                    "intent":None}
                }
    elif user_input_text in DATA_SOURCE_PHRASES: #where i got the data
        result = conversation_registry.data_source_route(user_input,session_state)
    elif user_input_text in AVAILABLE_DATA_PHRASES: #what data is available to query or run analytics over
        result = conversation_registry.available_data_inquiry_route(user_input,session_state)
    else: # let Claude chooses to call the tool
        start_time = datetime.now()
        message_content = summaries.run_tool_prompt(CONVERSATION_TOOLS , message)
        end_time = datetime.now()
        duration = end_time - start_time
        print(f"Conversation Route Duration:   {duration}")
        result = None
        # Python executes the tool
        for block in message_content:
            if block.type == "tool_use":
                start_time = datetime.now()
                tool = get_conversation_tool(block.name)
                tool_input = dict(block.input)
                tool_input["session_state"] = session_state
                result = tool["function"](**tool_input)
                end_time = datetime.now()
                duration = end_time - start_time
                print(f"Conversation Tool Duration:   {duration}")
                break
        if result is None:
            raise ValueError(f"Claude did not call a conversation tool. Response was: {message_content}")


    return result