import google.generativeai as genai
import os
import sys

# 1. Get the API Key from the environment variable
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    print("❌ Error: GEMINI_API_KEY environment variable not set.")
    print("👉 Please run: export GEMINI_API_KEY='your_actual_key_here'")
    sys.exit(1)

# 2. Configure the library
try:
    genai.configure(api_key=api_key)
    
    # 3. Initialize the model
    # Using gemini-1.5-flash for speed and efficiency
    model = genai.GenerativeModel('gemini-1.5-flash')

    # 4. Get the prompt from command line arguments
    prompt = " ".join(sys.argv[1:])
    if not prompt:
        prompt = "Hello! Tell me a one-sentence fun fact."

    print(f"🤖 Asking Gemini: '{prompt}'...\n")

    # 5. Generate content
    response = model.generate_content(prompt)
    print(response.text)

except Exception as e:
    print(f"❌ An error occurred: {e}")
