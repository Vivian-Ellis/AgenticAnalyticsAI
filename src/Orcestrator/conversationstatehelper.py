import sys
from pathlib import Path
from dotenv import load_dotenv
# import orcestrator
import os
import joblib
import json

BASE_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.abspath(
    os.path.join(BASE_DIR,
        "..",
        "..",
        "data",
        "log_regression_route_classifier.joblib"))

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.append(str(SRC_DIR))

env_path = PROJECT_ROOT / ".env"
load_dotenv(env_path, override=True)

ROUTING_MODEL = joblib.load(MODEL_PATH)

with open("data/date_labels.json", "r") as f:
    DATE_LABELS = json.load(f)

def date_cleanup(table):
    for grain in ["WEEK", "MONTH", "QUARTER"]:
        if grain in table.columns:
            table[grain] = (
                table[grain]
                .astype(str)
                .map(DATE_LABELS[grain]))

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

from Tools import conversation_tool_registry
from Tools import conversation_registry

def question_routing(user_input,metadata,chat_history=None):
    route = ROUTING_MODEL.predict([user_input])[0]
    tool=conversation_tool_registry.get_conversation_tool(route)
    return tool["function"](user_input,metadata,chat_history)

#     if route == "analytics":
#         agentresponse = orcestrator.run_analytics_agent(user_input)
#         return {
#             "summary": clean_llm_markdown(agentresponse.response['summary']),
#             "chart_path": agentresponse.response['chart_path'],
#             "table": agentresponse.response['table'],
#             "metadata": {"route": "analytics",
#                          "intent":agentresponse.response["metadata"]["intent"]}
#         }

#     elif route == "greeting":
#         return {
#             "summary": "Hi, I'm ready to answer questions about FRED data.",
#             "chart_path": None,
#             "table": None,
#             "metadata": {"route": "greeting",
#                          "intent":None}
#         }

#     elif route in ["metadata", "other"]:
#         response = orcestrator.run_general_agent(user_input, metadata, chat_history)
#         return {
#             "summary": clean_llm_markdown(response),
#             "chart_path": None,
#             "table": None,
#             "metadata": {"route": route,
#                          "intent":None}
#         }