import sys
from pathlib import Path
from dotenv import load_dotenv

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.append(str(SRC_DIR))

env_path = PROJECT_ROOT / ".env"
load_dotenv(env_path, override=True)

import orcestrator
import html
import DataBase.db as db
from Orcestrator.questionrouter import route_message

@st.cache_data(show_spinner=False)
def load_metadata():
    return db.get_series_metadata()

metadata = load_metadata()[["series_id","title","frequency","observation_start","observation_end"]].to_markdown(index=False)

import os
import joblib
BASE_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.abspath(
    os.path.join(
        BASE_DIR,
        "..",
        "..",
        "data",
        "log_regression_route_classifier.joblib"
    )
)
ROUTING_MODEL = joblib.load(MODEL_PATH)

def question_routing(user_input, chat_history=None):
    route = ROUTING_MODEL.predict([user_input])[0]

    if route == "analytics":
        agentresponse = orcestrator.run_analytics_agent(user_input)
        return agentresponse.response

    elif route == "greeting":
        return {
            "summary": "Hi, I'm ready to answer questions about FRED data.",
            "chart_path": None,
            "table": None,
            "metadata": {"intent": "greeting"}
        }

    elif route in ["metadata", "other"]:
        response = orcestrator.run_general_agent(user_input, metadata, chat_history)
        return {
            "summary": response,
            "chart_path": None,
            "table": None,
            "metadata": {"intent": route}
        }

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


# initialize memory
if "messages" not in st.session_state:
    st.session_state.messages = []

st.markdown(
    """
    <style>
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
    }
    .stButton > button {
        border-radius: 28px;
    }

    [data-testid="stSidebar"] {
        border-right: 1px solid #EEE7E1;
    }

    /* hide avatars */
    [data-testid="stChatMessageAvatarUser"],
    [data-testid="stChatMessageAvatarAssistant"] {
        display: none !important;
    }

    /* tighten spacing */
    [data-testid="stChatMessage"] {
        gap: 0rem !important;
    }

    /* user message bubble */
    [data-testid="stChatMessage"]:has(.user-message) {
        background-color: #F9F1EC;
        border-radius: 18px;
    }

    /* =========================
       CHAT INPUT
       ========================= */

    [data-testid="stChatInput"] {
        background-color: #F9F1EC !important;

        border-radius: 999px !important;

        border: 1px solid #EEE2DA !important;

        padding:
            0.35rem
            0.45rem
            0.35rem
            1rem !important;

        box-shadow:
            0 3px 12px rgba(0,0,0,0.05) !important;
    }

    /* remove inner backgrounds */
    [data-testid="stChatInput"] * {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }

    /* textarea */
    [data-testid="stChatInput"] textarea {
        color: #1D1D19 !important;

        font-size: 15px !important;

        line-height: 1.4 !important;

        padding-top: 0.55rem !important;

        min-height: 24px !important;
    }

    /* placeholder */
    [data-testid="stChatInput"] textarea::placeholder {
        color: #8C7F78 !important;
        opacity: 1 !important;
    }

    /* send button */
    [data-testid="stChatInput"] button {
        background-color: rgba(255,255,255,0.58) !important;

        border-radius: 999px !important;

        height: 2.15rem !important;
        width: 2.15rem !important;

        transition: all 0.15s ease;
    }

    [data-testid="stChatInput"] button:hover {
        background-color: rgba(255,255,255,0.78) !important;
    }

    /* send icon */
    [data-testid="stChatInput"] svg {
        color: #756963 !important;
    }

    </style>
    """,
    unsafe_allow_html=True,
)
# st.markdown(
#     """
#     <style>

#     .stButton > button {
#         border-radius: 28px;
#     }

#     [data-testid="stSidebar"] {
#         border-right: 1px solid #edeae1;
#     }

#     /* hide all chat avatars */
#     [data-testid="stChatMessageAvatarUser"],
#     [data-testid="stChatMessageAvatarAssistant"] {
#         display: none !important;
#     }

#     /* remove avatar spacing */
#     [data-testid="stChatMessage"] {
#         gap: 0rem !important;
#     }

#     /* user messages only */
#     [data-testid="stChatMessage"]:has(.user-message) {
#         background-color: #edeae1;
#         border-radius: 16px;
#     }
#     </style>
#     """,
#     unsafe_allow_html=True,
# )

# chat box at bottom
user_input = st.chat_input("Ask anything...", key="chat_input")

# intro message only on a fresh chat before first input
if len(st.session_state.messages) == 0 and not user_input:
    st.write("Ask me anything about the Federal Reserve Economic Data (FRED).")

# render existing chat history
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user", avatar=None):
            st.markdown(
                f'<p class="user-message">{msg["content"]}</p>',
                unsafe_allow_html=True,
            )
    else:
        with st.chat_message("assistant", avatar=None):
            st.write(msg["content"])

# handle new input
if user_input:
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    # immediately show user message
    with st.chat_message("user", avatar=None):
        st.markdown(
            f'<p class="user-message">{user_input}</p>',
            unsafe_allow_html=True,
        )

    # generate assistant response
    with st.chat_message("assistant", avatar=None):
        with st.spinner("Analyzing..."):
            # agentresponse = orcestrator.run_agent(user_input)
            # response = agentresponse.response["summary"]
            result=question_routing(user_input)
            response = result["summary"]
            intent = result["metadata"]["intent"]

            if intent == "ranking":
                if result["table"] is not None:
                    table = result["table"].copy()
                    table.index = table.index + 1
                    table.index.name = "Rank"

                    st.dataframe(
                        table,
                        use_container_width=True,
                        height=280
                    )

                if result["chart_path"]:
                    st.image(result["chart_path"])

                st.markdown(clean_llm_markdown(response))

            else:
                st.markdown(clean_llm_markdown(response))

                if result["chart_path"]:
                    st.image(result["chart_path"])

                if result["table"] is not None:
                    st.dataframe(
                        result["table"],
                        use_container_width=True,
                        hide_index=True
                    )

        st.session_state.messages.append({"role": "assistant",
                                            "content": response,
                                            "result": result})