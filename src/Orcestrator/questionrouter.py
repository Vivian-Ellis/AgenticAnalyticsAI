# src/Orcestrator/message_router.py
import sys
sys.path.append("../src/")
import Narration.summaries as summaries
import os

def route_message(question,chat_history=None):
    chat_history = chat_history or []
    recent_history = chat_history[-6:]
    
    response=summaries.run_question_router(question,recent_history)

    route = response.strip().lower()

    if route not in {"analytics", "other"}:
        return "other"

    return route