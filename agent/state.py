# -----------------------------
# IMPORTS + ENV SETUP
# -----------------------------
from dotenv import load_dotenv
import os
from openai import OpenAI
from groq import Groq
from agent.memory import Memory

memory = Memory()
load_dotenv()

# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
# -----------------------------
# STATE DEFINITION
# -----------------------------
state = {
    "portfolio_id": None,

    # data layer
    "exposure": None,

    # analysis layer
    "risk_level": None,

    # decision layer
    "decision": None,

    # execution tracking
    "steps": {
        "fetch_data": "pending",
        "analyze": "pending",
        "decide": "pending"
    }
}


# -----------------------------
# STEP 1: FETCH DATA
# -----------------------------
def fetch_data(state):
    if state["steps"]["fetch_data"] == "done":
        print("Skipping fetch_data (already done)")
        return state

    print("Running fetch_data...")

    # simulate data fetch
    state["exposure"] = 1200000  

    state["steps"]["fetch_data"] = "done"
    return state


# -----------------------------
# STEP 2: ANALYZE RISK (LLM)
# -----------------------------
def analyze_risk(state):
    if state["steps"]["analyze"] == "done":
        print("Skipping analyze_risk (already done)")
        return state

    print("Running analyze_risk with LLM...")

    exposure = state["exposure"]

    prompt = f"""
    You are a credit risk analyst.

    Exposure: {exposure}

    Rule:
    - Above 1,000,000 = HIGH
    - Otherwise = LOW

    Respond ONLY with: HIGH or LOW
    """

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )

    output = response.choices[0].message.content.strip()

    if "HIGH" in output.upper():
        state["risk_level"] = "High"
    else:
        state["risk_level"] = "Low"

    state["steps"]["analyze"] = "done"
    return state


# -----------------------------
# STEP 3: DECISION
# -----------------------------
def make_decision(state):
    if state["steps"]["decide"] == "done":
        print("Skipping decision (already done)")
        return state

    print("Running decision step...")

    if state["risk_level"] == "High":
        state["decision"] = "Reduce exposure"
    else:
        state["decision"] = "Maintain position"

    state["steps"]["decide"] = "done"
    return state


# -----------------------------
# RUNNER
# -----------------------------
def run_agent(state):
    state = fetch_data(state)
    state = analyze_risk(state)
    state = make_decision(state)
    return state


# -----------------------------
# TEST
# -----------------------------
if __name__ == "__main__":
    state["portfolio_id"] = "PF123"

    result = run_agent(state)

    print("\nFinal State:")
    for k, v in result.items():
        print(f"{k}: {v}")