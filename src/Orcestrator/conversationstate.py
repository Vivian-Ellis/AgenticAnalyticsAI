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

from datetime import datetime
import time

#pull the FRED metadata for available datasets
@st.cache_data(show_spinner=False)
def load_metadata():
    return db.get_series_metadata()

st.session_state.fred_metadata = load_metadata()[["series_id","title","frequency","observation_start","observation_end","description","updated_title","seasonal_adjustment"]]

markdown_style = Path("appmarkdownstyle.txt").read_text()

#sytling and helpful info for newbies
HELP_MESSAGE = """I'm here to provide statistical analysis of Federal Reserve Economic Data (FRED). 

**📈 Trends**
- How has payroll employment changed over time?
- When did inflation begin accelerating?

**🏆 Rankings**
- Top 5 unemployment years
- Lowest GDP quarters over the past 10 years.

**⚖️ Comparisons**
- Compare median employment levels before and after COVID.
- Compare unemployment volatility between 2024 and 2025.

**🔗 Correlations**
- Is there a relationship between interest rates and unemployment?
- How strongly are GDP and employment levels correlated?

**📚 Metadata**
- What datasets are available?
- What does CPI mean?

**🔄 Follow-ups**
- Now do GDP
- Make it monthly
- Bottom 6 instead

**💡Clarifications**
- Why did you use Spearman?
- Explain the p-value.
"""

col1, col2 = st.columns([5, 1])

# with col1:
#     st.write("### FRED Analytics AI Agent")

with col2:
    with st.popover("Help",icon="❔"):
        st.markdown(HELP_MESSAGE)
# end help message

def markdown_table(table,analysis_type):
    #for rank
    if table is not None:
        table=helper.markdown_table_helper(table,analysis_type)
        if analysis_type=="ranking":
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
    intent = msg.get("data_plan", {}).get("intent")
    
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

# initialize starting_suggestions
if "starting_suggestions" not in st.session_state:
    st.session_state.starting_suggestions = None

#new chat with the suggestion selected
if not user_input and st.session_state.get("starting_suggestions"):
        basic_suggestion=st.session_state.starting_suggestions
        if basic_suggestion=="📊 Interest rates & Unemployment Correlation":
            user_input = "Is there a relationship between interest rates and unemployment?"
        elif basic_suggestion=="📈GDP Trends":
            user_input = "Analyse how GDP trends have changed over time."
        elif basic_suggestion=="🏆 Top 5 Unemployment Years":
            user_input = "Rank the top 5 unemployment years."
        elif basic_suggestion=="⚖️ Inflation: 2024 vs 2025":
            user_input = "Was inflation higher in 2024 than in 2025?"
        elif basic_suggestion=="🗃️ Available Datasets":
            user_input = "What are the available FRED datasets?"

# intro message only on a fresh chat before first user input
if len(st.session_state.messages) == 0 and not user_input:
    st.write("Ask me anything about the Federal Reserve Economic Data (FRED).")

    #provide suggestions only on a new chat
    selection = st.pills("Suggestions", 
                         ["📈GDP Trends","📊 Interest rates & Unemployment Correlation","🏆 Top 5 Unemployment Years","⚖️ Inflation: 2024 vs 2025","🗃️ Available Datasets"],
                         label_visibility="hidden",
                         key="starting_suggestions")

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
            # Record time
            start_time = datetime.now()
            result=helper.question_routing(user_input=user_input,session_state=st.session_state)
            end_time = datetime.now()
            duration = end_time - start_time
            print(f"Duration:   {duration}")
            assistant_msg = {
                "role": "assistant",
                "content": result["summary"],
                "data_plan": result.get("data_plan", {}),
                "methodology_reasoning": result.get("methodology_reasoning", {}),
                "table": result.get("table"),
                "chart_path": result.get("chart_path")}

            render_assistant_message(assistant_msg)
            # print(assistant_msg)
        # append to chat history
        st.session_state.messages.append(assistant_msg)