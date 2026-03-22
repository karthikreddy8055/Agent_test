from dotenv import load_dotenv
import os
from groq import Groq
from agent.memory import Memory
import uuid

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
memory = Memory()



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
        
        
        summary = summarize_for_memory(answer)

        if should_store(user_input, answer) and not memory.exists(summary):
            memory.add(
                text=summary,
                metadata={"type": "concept"}
            )



if __name__ == "__main__":
    chat()