from dotenv import load_dotenv
import os
from groq import Groq
from agent.memory import Memory
import uuid
import json
from agent.tools.risk_tools import analyze_portfolio

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
memory = Memory()
def tool_decision_agent(user_input):
    prompt = f"""
You are a tool routing agent.

Available tools:
1. analyze_portfolio(portfolio_id) → analyzes portfolio risk

User Query:
{user_input}

Decide:
- Should a tool be used?
- If yes, which tool?
- Extract required arguments

Return STRICT JSON ONLY:

{{
  "use_tool": true/false,
  "tool": "tool_name or null",
  "arguments": {{
    "portfolio_id": "value if applicable"
  }}
}}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content.strip()


def memory_agent(user_input, answer, existing_context):
    prompt = f"""
    You are a memory decision agent.

    Your job is to decide whether the following information should be stored in long-term memory.

    Existing Memory:
    {existing_context}

    New Information:
    User Query: {user_input}
    Agent Response: {answer}

    Rules:
    - Store ONLY core, generalizable concepts (definitions, key principles)
    - Do NOT store expanded explanations if a simpler version already exists
    - Do NOT store system-related or assistant capability descriptions
    - Avoid storing multiple variations of the same concept
    - Prefer the most concise version of knowledge
    - ONLY store knowledge related to financial risk, credit risk, or financial concepts
    - DO NOT store unrelated or conversational observations

    If similar knowledge already exists, return store=false

Return ONLY 1 short sentence if storing
    Return STRICT JSON ONLY:
    {{
    "store": true or false,
    "content": "clean summary if store is true"
    }}
    """
    
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content.strip()


def should_store(user_input, answer):
    user_input = user_input.lower()

    if user_input in ["hi", "hello", "hey"]:
        return False

    if len(answer) < 50:
        return False

    if "thank" in user_input:
        return False

    return True


def summarize_for_memory(answer):
    return answer.split(".")[0]  # keep first sentence only



def build_prompt(user_input, context):
    return f"""
You are a financial risk assistant.

Context (use only if relevant):
{context}

User Query:
{user_input}

Instructions:
- Be precise
- Use business language
- Ignore irrelevant context

Answer:
"""


def chat():
    print("Agent started. Type 'exit' to stop.\n")
    
    while True:
        user_input = input("You: ")

        if user_input.lower() == "exit":
            break

        # 🔹 TOOL ROUTING (v1)

        # user_lower = user_input.lower()
        

        decision_raw = tool_decision_agent(user_input)

        try:
            decision = json.loads(decision_raw)
        except:
            decision = {"use_tool": False}

        if decision.get("use_tool"):
            tool = decision.get("tool")
            args = decision.get("arguments", {})

            if tool == "analyze_portfolio":
                portfolio_id = args.get("portfolio_id")

                if portfolio_id:
                    result = analyze_portfolio(portfolio_id)

                    tool_context = f"""
        Portfolio Analysis Result:
        Portfolio ID: {result['portfolio_id']}
        Exposure: {result['exposure']}
        Risk Level: {result['risk']}
        Decision: {result['decision']}
        """

                    prompt = f"""
        You are a financial risk analyst.

        Use ONLY the following tool output:

        {tool_context}

        User Query:
        {user_input}

        Instructions:
        - Do NOT add assumptions
        - Do NOT invent numbers
        - Be concise and factual

        Answer:
        """

                    response = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[{"role": "user", "content": prompt}]
                    )

                    answer = response.choices[0].message.content.strip()

                    print(f"\nAgent: {answer}\n")

                    continue

        # if "portfolio" in user_lower:
        #     # extract portfolio id (simple version)
        #     words = user_input.split()
        #     portfolio_id = None

        #     for w in words:
        #         if w.upper().startswith("PF"):
        #             portfolio_id = w
        #             break

        #     if portfolio_id:
        #         result = analyze_portfolio(portfolio_id)

        #         tool_context = f"""
        #         Portfolio Analysis Result:
        #         Portfolio ID: {result['portfolio_id']}
        #         Exposure: {result['exposure']}
        #         Risk Level: {result['risk']}
        #         Decision: {result['decision']}
        #         """

        #         prompt = f"""
        #         You are a financial risk analyst.

        #         Use the following tool output to explain the situation clearly in business terms.

        #         {tool_context}

        #         User Query:
        #         {user_input}

        #         Instructions:
        #         - Be concise
        #         - Use ONLY the provided tool output
        #         - Do NOT assume or add external information
        #         - Do NOT invent numbers or percentages
        #         - Be concise and factual
        #         - Explain risk and decision clearly based on given data only

        #         Answer:
        #         """

        #         response = client.chat.completions.create(
        #             model="llama-3.1-8b-instant",
        #             messages=[{"role": "user", "content": prompt}]
        #         )

        #         answer = response.choices[0].message.content.strip()

        #         print(f"\nAgent: {answer}\n")

        #         continue



        # 🔹 Retrieve memory
        results = memory.search(user_input)
        documents = results.get("documents", [[]])[0]
        distances = results.get("distances", [[]])[0]

        filtered_docs = []

        for doc, dist in zip(documents, distances):
            if dist < 1.2:  # threshold (tune later)
                filtered_docs.append(doc)
        filtered_docs = filtered_docs[:2]
        context = "\n".join(filtered_docs) if filtered_docs else "No relevant past information"


        # 🔹 Build prompt
        prompt = build_prompt(user_input, context)

        # 🔹 LLM call
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}]
        )

        answer = response.choices[0].message.content.strip()

        print(f"\nAgent: {answer}\n")

        # 🔹 Store interaction
        
    
        decision_raw = memory_agent(user_input, answer, context)

        try:
            decision = json.loads(decision_raw)
        except:
            decision = {"store": False}

        if decision.get("store"):
            content = decision.get("content", "").strip()

            if content and not memory.exists(content):
                memory.add(
                    text=content,
                    metadata={"type": "concept"}
                )



if __name__ == "__main__":
    chat()