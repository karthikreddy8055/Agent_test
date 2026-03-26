import streamlit as st
from agent.chat_agent import process_input

st.set_page_config(page_title="Agent UI", layout="wide")

st.markdown("""
<style>
    .main {
        background-color: #0e1117;
    }
    .stChatMessage {
        border-radius: 12px;
        padding: 10px;
        margin-bottom: 10px;
    }
    .user-msg {
        background-color: #1f2937;
    }
    .assistant-msg {
        background-color: #111827;
    }
    .header-title {
        font-size: 36px;
        font-weight: 700;
        color: #f9fafb;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="header-title">🧠 Financial Risk Agent</div>', unsafe_allow_html=True)

def format_response(response: str) -> str:
    response_lower = response.lower()

    if "portfolio" in response_lower or "risk" in response_lower:
        formatted = "### 📊 Portfolio Summary\n\n"

        lines = response.split("\n")

        for line in lines:
            clean = line.strip()
            if not clean:
                continue

            if "risk" in clean.lower():
                if "high" in clean.lower():
                    formatted += f"- 🔴 **{clean}**\n"
                else:
                    formatted += f"- 🟢 **{clean}**\n"

            elif "exposure" in clean.lower():
                formatted += f"- 💰 **{clean}**\n"

            elif "decision" in clean.lower() or "recommend" in clean.lower():
                formatted += f"- ⚡ **{clean}**\n"

            else:
                formatted += f"- {clean}\n"

        return formatted

    return response

# session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# display previous messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant":
            st.markdown(format_response(msg["content"]))
        else:
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
        st.markdown(format_response(response))

    st.session_state.messages.append({"role": "assistant", "content": response})