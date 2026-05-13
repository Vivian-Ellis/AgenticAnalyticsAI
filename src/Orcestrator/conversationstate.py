import sys
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.append(str(SRC_DIR))
env_path = PROJECT_ROOT / ".env"
load_dotenv(env_path, override=True)

import DataBase.db as db
import conversationstatehelper as helper
import streamlit as st
from streamlit_bokeh import streamlit_bokeh

@st.cache_data(show_spinner=False)
def load_metadata():
    return db.get_series_metadata()

metadata = load_metadata()[["series_id","title","frequency","observation_start","observation_end"]].to_markdown(index=False)

markdown_style = Path("appmarkdownstyle.txt").read_text()

def markdown_table(table,analysis_type):
    #for rank
    if table is not None:
        if analysis_type=="ranking":
            table = table.copy()
            table.index = table.index + 1
            table.index.name = "Rank"
            # human readable dates
            helper.date_cleanup(table)
            # format header
            table.columns = [col.replace("_", " ").title() for col in table.columns]
            #round values
            table["Value"] = table["Value"].round(2)
            # display table to chat
            st.dataframe(table,width="stretch")
        else:
            st.dataframe(table,width='stretch',hide_index=True)

def markdown_chart(chart):
    if chart:
        streamlit_bokeh(chart)

def render_assistant_message(msg):
    content = msg.get("content")
    table = msg.get("table")
    chart = msg.get("chart_path")
    intent = msg.get("metadata", {}).get("intent")

    if intent == "ranking":
        # prints all three respectively: ranked table, chart, and short summary
        markdown_table(table, intent)
        markdown_chart(chart)
        st.markdown(content)
    else:
        # prints all three respectively: full summary, chart, and table
        st.markdown(content)
        markdown_chart(chart)
        markdown_table(table, intent)

# initialize memory
if "messages" not in st.session_state:
    st.session_state.messages = []

#set the ccs stylings
st.markdown(markdown_style,unsafe_allow_html=True)

# input text box at bottom
user_input = st.chat_input("Ask anything...", key="chat_input")

# intro message only on a fresh chat before first user input
if len(st.session_state.messages) == 0 and not user_input:
    st.write("Ask me anything about the Federal Reserve Economic Data (FRED).")

# render existing chat history
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user", avatar=None):
            st.markdown(f'<p class="user-message">{msg["content"]}</p>',unsafe_allow_html=True)
    else:
        with st.chat_message("assistant", avatar=None):
            # st.write(msg["content"])
            render_assistant_message(msg)

# handling new user input
if user_input:
    st.session_state.messages.append({"role": "user","content": user_input})

    # immediately show user message
    with st.chat_message("user", avatar=None):
        st.markdown(f'<p class="user-message">{user_input}</p>',unsafe_allow_html=True)

    # generate assistant response
    with st.chat_message("assistant", avatar=None):
        with st.spinner("Analyzing..."):
            result=helper.question_routing(user_input=user_input,
                                           metadata=metadata,
                                           chat_history=st.session_state.messages)
            assistant_msg = {
                "role": "assistant",
                "content": result["summary"],
                "metadata": result.get("metadata", {}),
                "table": result.get("table"),
                "chart_path": result.get("chart_path")}

            render_assistant_message(assistant_msg)

        # append to chat history
        st.session_state.messages.append(assistant_msg)