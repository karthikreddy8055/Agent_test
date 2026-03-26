import streamlit as st
from agent.chat_agent import process_input

st.set_page_config(page_title="Agent UI", layout="wide")

st.title("🧠 Financial Risk Agent")

# session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# display previous messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# user input
user_input = st.chat_input("Ask something...")

if user_input:
    # display user message
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    # 🔹 CALL AGENT (we’ll modify this)
    with st.spinner("Analyzing..."):
        response = process_input(user_input)

    # display agent response
    with st.chat_message("assistant"):
        st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})