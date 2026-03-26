from dotenv import load_dotenv
import os
import json
from groq import Groq
from agent.memory import Memory
from agent.tools.risk_tools import analyze_portfolio, calculate_var

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
memory = Memory()
last_tool_result_global = None


# -----------------------------
# TOOL DECISION AGENT
# -----------------------------
def tool_decision_agent(user_input):
    prompt = f"""
You are a strict tool routing agent.

Available tools:

1. analyze_portfolio(portfolio_id)
   → Use for: ANY portfolio-related query (risk, exposure, analysis)

2. calculate_var(portfolio_id)
   → Use for: VaR, value at risk, loss estimation

STRICT RULES:
- If a portfolio ID (e.g., PF123) is mentioned → ALWAYS use a tool
- DO NOT answer using your own knowledge
- DO NOT ask for more information
- DO NOT make assumptions
- If portfolio-related → use analyze_portfolio
- If VaR-related → use calculate_var

User Query:
{user_input}

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


def process_input(user_input):
    global last_tool_result_global

    user_lower = user_input.lower()

    # =============================
    # 🔹 0. HARD RULE: VaR TOOL
    # =============================
    if "var" in user_lower or "value at risk" in user_lower:

        portfolio_id = None
        words = user_input.split()

        for w in words:
            if w.lower().startswith("pf"):
                portfolio_id = w.upper()
                break

        if not portfolio_id and last_tool_result_global:
            portfolio_id = last_tool_result_global["portfolio_id"]

        if portfolio_id:
            result = calculate_var(portfolio_id)

            tool_context = f"""
VaR Result:
Portfolio ID: {result['portfolio_id']}
VaR (95%): {result['var_95']}
Confidence: {result['confidence']}
"""

            prompt = f"""
You are a financial risk analyst.

Use ONLY the following tool output:

{tool_context}

User Query:
{user_input}

Instructions:
- Do NOT assume anything beyond this data
- Be concise

Answer:
"""

            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}]
            )

            return response.choices[0].message.content.strip()

    # =============================
    # 🔹 1. TOOL DECISION
    # =============================
    decision_raw = tool_decision_agent(user_input)

    try:
        decision = json.loads(decision_raw)
    except:
        decision = {"use_tool": False}

    # =============================
    # 🔹 2. FALLBACK GUARDRAIL
    # =============================
    if not decision.get("use_tool"):

        if "pf" in user_lower:
            decision["use_tool"] = True

            if "var" in user_lower:
                decision["tool"] = "calculate_var"
            else:
                decision["tool"] = "analyze_portfolio"

            for w in user_input.split():
                if w.lower().startswith("pf"):
                    decision["arguments"] = {"portfolio_id": w.upper()}
                    break

    # =============================
    # 🔹 3. TOOL EXECUTION
    # =============================
    if decision.get("use_tool"):
        tool = decision.get("tool")
        args = decision.get("arguments", {})

        portfolio_id = args.get("portfolio_id")

        if portfolio_id:
            portfolio_id = portfolio_id.upper()

        if tool == "analyze_portfolio" and portfolio_id:
            result = analyze_portfolio(portfolio_id)
            last_tool_result_global = result

            tool_context = f"""
Portfolio Analysis Result:
Portfolio ID: {result['portfolio_id']}
Exposure: {result['exposure']}
Risk Level: {result['risk']}
Decision: {result['decision']}
"""

        elif tool == "calculate_var" and portfolio_id:
            result = calculate_var(portfolio_id)

            tool_context = f"""
VaR Result:
Portfolio ID: {result['portfolio_id']}
VaR (95%): {result['var_95']}
Confidence: {result['confidence']}
"""

        else:
            tool_context = None

        if tool_context:
            prompt = f"""
You are a financial risk analyst.

Use ONLY the following tool output:

{tool_context}

User Query:
{user_input}

Instructions:
- Use ONLY provided data
- Do NOT add assumptions
- Be concise and business-focused

Answer:
"""

            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}]
            )

            return response.choices[0].message.content.strip()

    # =============================
    # 🔹 4. SESSION MEMORY
    # =============================
    if last_tool_result_global:

        tool_context = f"""
Portfolio Analysis Result:
Portfolio ID: {last_tool_result_global['portfolio_id']}
Exposure: {last_tool_result_global['exposure']}
Risk Level: {last_tool_result_global['risk']}
Decision: {last_tool_result_global['decision']}
"""

        prompt = f"""
You are a financial risk analyst.

Use ONLY the following previously known information:

{tool_context}

User Query:
{user_input}

Instructions:
- Use ONLY the provided portfolio information
- Do NOT give generic definitions
- Do NOT assume or invent data
- Be concise

Answer:
"""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}]
        )

        return response.choices[0].message.content.strip()

    # =============================
    # 🔹 5. SAFE DEFAULT
    # =============================
    prompt = f"""
You are a financial assistant.

User Query:
{user_input}

Instructions:
- If unsure, ask for clarification
- Do NOT make assumptions

Answer:
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content.strip()


# -----------------------------
# CONTEXT DECISION AGENT
# -----------------------------
def context_decision_agent(user_input):
    prompt = f"""
You are a context decision agent.

Determine if the user query depends on previously discussed portfolio context.

Context-dependent examples:
- what is the risk
- what should we do
- tell me more about it

General examples:
- what is exposure definition
- explain credit risk

User Query:
{user_input}

Return STRICT JSON:

{{
  "use_context": true/false
}}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content.strip()


# -----------------------------
# CHAT LOOP
# -----------------------------
def chat():
    print("Agent started. Type 'exit' to stop.\n")
    chat_history = []

    last_tool_result = None

    while True:
        try:
            user_input = input("You: ")
        except EOFError:
            break

        if user_input.lower() == "exit":
            break

        user_lower = user_input.lower()

        # =============================
        # 🔹 0. HARD RULE: VaR TOOL
        # =============================
        if "var" in user_lower or "value at risk" in user_lower:

            portfolio_id = None
            words = user_input.split()

            for w in words:
                if w.lower().startswith("pf"):
                    portfolio_id = w.upper()
                    break

            # fallback to last known portfolio
            if not portfolio_id and last_tool_result:
                portfolio_id = last_tool_result["portfolio_id"]

            if portfolio_id:
                result = calculate_var(portfolio_id)

                tool_context = f"""
VaR Result:
Portfolio ID: {result['portfolio_id']}
VaR (95%): {result['var_95']}
Confidence: {result['confidence']}
"""

                prompt = f"""
You are a financial risk analyst.

Use ONLY the following tool output:

{tool_context}

User Query:
{user_input}

Instructions:
- Do NOT assume anything beyond this data
- Be concise

Answer:
"""

                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages = [{"role": "user", "content": prompt}]
                )

                answer = response.choices[0].message.content.strip()
                print(f"\nAgent: {answer}\n")
                chat_history.append({"role": "user", "content": user_input})
                chat_history.append({"role": "assistant", "content": answer})
                continue

        # =============================
        # 🔹 1. TOOL DECISION (LLM)
        # =============================
        decision_raw = tool_decision_agent(user_input)

        try:
            decision = json.loads(decision_raw)
        except:
            decision = {"use_tool": False}

        # =============================
        # 🔹 2. FALLBACK GUARDRAIL
        # =============================
        if not decision.get("use_tool"):

            if "pf" in user_lower:
                decision["use_tool"] = True

                if "var" in user_lower:
                    decision["tool"] = "calculate_var"
                else:
                    decision["tool"] = "analyze_portfolio"

                words = user_input.split()
                for w in words:
                    if w.lower().startswith("pf"):
                        decision["arguments"] = {"portfolio_id": w.upper()}
                        break

        # =============================
        # 🔹 3. TOOL EXECUTION
        # =============================
        if decision.get("use_tool"):
            tool = decision.get("tool")
            args = decision.get("arguments", {})

            portfolio_id = args.get("portfolio_id")

            if portfolio_id:
                portfolio_id = portfolio_id.upper()

            # -------- analyze_portfolio --------
            if tool == "analyze_portfolio" and portfolio_id:
                result = analyze_portfolio(portfolio_id)
                last_tool_result = result

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
- Use ONLY provided data
- Do NOT add assumptions
- Be concise and business-focused

Answer:
"""

            # -------- calculate_var --------
            elif tool == "calculate_var" and portfolio_id:
                result = calculate_var(portfolio_id)

                tool_context = f"""
VaR Result:
Portfolio ID: {result['portfolio_id']}
VaR (95%): {result['var_95']}
Confidence: {result['confidence']}
"""

                prompt = f"""
You are a financial risk analyst.

Use ONLY the following tool output:

{tool_context}

User Query:
{user_input}

Instructions:
- Do NOT assume anything beyond this data
- Be concise

Answer:
"""

            else:
                prompt = None

            if prompt:
                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages = [{"role": "user", "content": prompt}]
                )

                answer = response.choices[0].message.content.strip()
                print(f"\nAgent: {answer}\n")
                chat_history.append({"role": "user", "content": user_input})
                chat_history.append({"role": "assistant", "content": answer})
                continue

        # =============================
        # 🔹 4. SESSION MEMORY
        # =============================
        use_context = False

        if last_tool_result:
            decision_raw = context_decision_agent(user_input)

            try:
                decision = json.loads(decision_raw)
                use_context = decision.get("use_context", False)
            except:
                use_context = False

        if last_tool_result and use_context:

            tool_context = f"""
Portfolio Analysis Result:
Portfolio ID: {last_tool_result['portfolio_id']}
Exposure: {last_tool_result['exposure']}
Risk Level: {last_tool_result['risk']}
Decision: {last_tool_result['decision']}
"""

            prompt = f"""
You are a financial risk analyst.

Use ONLY the following previously known information:

{tool_context}

User Query:
{user_input}

Instructions:
- Use ONLY the provided portfolio information
- Answer specifically for this portfolio
- Do NOT give generic definitions
- Do NOT add external explanations
- Do NOT assume or invent any data
- Do NOT derive or calculate new values
- Be concise

Answer:
"""

            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages = [{"role": "user", "content": prompt}]
            )

            answer = response.choices[0].message.content.strip()
            print(f"\nAgent: {answer}\n")
            chat_history.append({"role": "user", "content": user_input})
            chat_history.append({"role": "assistant", "content": answer})
            continue

        # =============================
        # 🔹 5. SAFE DEFAULT LLM
        # =============================
        prompt = f"""
You are a financial assistant.

User Query:
{user_input}

Instructions:
- If unsure, ask for clarification
- Do NOT make assumptions
- Do NOT fabricate financial analysis

Answer:
"""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages = chat_history + [{"role": "user", "content": prompt}]
        )

        answer = response.choices[0].message.content.strip()
        print(f"\nAgent: {answer}\n")
        chat_history.append({"role": "user", "content": user_input})
        chat_history.append({"role": "assistant", "content": answer})


# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    chat()