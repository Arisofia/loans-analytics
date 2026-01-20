from google import genai
import os
import sys

# 1. Setup
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    sys.exit("❌ Error: GEMINI_API_KEY environment variable not set.")

client = genai.Client(api_key=api_key)
model_id = "gemini-2.5-flash"

# 2. Start Chat Session
# The SDK manages the history automatically in this object
chat = client.chats.create(model=model_id)

print(f"✨ Interactive Chat with Gemini ({model_id})")
print("👉 Type 'exit', 'quit', or press Ctrl+C to stop.\n")

# 3. Chat Loop
while True:
    try:
        user_input = input("\033[1;34mYou:\033[0m ") # Blue text for "You:"
        if user_input.lower() in ["exit", "quit"]:
            print("👋 Goodbye!")
            break
        
        if not user_input.strip():
            continue

        # In the new SDK, we use send_message
        response = chat.send_message(message=user_input)
        print(f"\033[1;32mGemini:\033[0m {response.text}\n") # Green text for "Gemini:"

    except Key    except Key    except Keyt(    except Key    excep    break
        pt Exc        p e:
        print(f"❌ Error: {e}")
