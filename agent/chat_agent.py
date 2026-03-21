from dotenv import load_dotenv
import os
from groq import Groq
from agent.memory import Memory
import uuid

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
memory = Memory()


def build_prompt(user_input, context):
    return f"""
You are a financial risk assistant.

Use past context if relevant.

Context:
{context}

User:
{user_input}

Respond clearly, concisely, in business language.
"""


def chat():
    print("Agent started. Type 'exit' to stop.\n")

    while True:
        user_input = input("You: ")

        if user_input.lower() == "exit":
            break

        # 🔹 Retrieve memory
        context = memory.search(user_input)

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
        memory.add(
            f"User: {user_input} | Agent: {answer}",
            str(uuid.uuid4())
        )


if __name__ == "__main__":
    chat()