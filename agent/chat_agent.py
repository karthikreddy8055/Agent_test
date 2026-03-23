from dotenv import load_dotenv
import os
from groq import Groq
from agent.memory import Memory
import uuid
import json

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
memory = Memory()
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
    
    memory.add(
        text="IFRS9 is a financial reporting standard for expected credit loss",
        metadata={"type": "concept"}
    )

    memory.add(
        text="Credit risk is the risk of default by a borrower",
        metadata={"type": "concept"}
)

    while True:
        user_input = input("You: ")

        if user_input.lower() == "exit":
            break



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