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

    .stButton > button {
        border-radius: 28px;
    }

    [data-testid="stSidebar"] {
        border-right: 1px solid #e6e1d6;
    }

    /* hide all chat avatars */
    [data-testid="stChatMessageAvatarUser"],
    [data-testid="stChatMessageAvatarAssistant"] {
        display: none !important;
    }

    /* remove avatar spacing */
    [data-testid="stChatMessage"] {
        gap: 0rem !important;
    }

    /* user messages only */
    [data-testid="stChatMessage"]:has(.user-message) {
        background-color: #f0ede4;
        border-radius: 16px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

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
            agentresponse = orcestrator.run_agent(user_input)
            response = agentresponse.response["summary"]

        st.markdown(clean_llm_markdown(response))

    st.session_state.messages.append({
        "role": "assistant",
        "content": response
    })

