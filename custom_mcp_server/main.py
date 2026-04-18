import os
from dotenv import load_dotenv
from google import genai

# Load API key
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def chat():
    print("CLI Chatbot (type 'exit' to quit)\n")

    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break

        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-preview",
            contents=user_input,
        )

        print("Bot:", response.text, "\n")

if __name__ == "__main__":
    chat()