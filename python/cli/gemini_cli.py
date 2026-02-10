import argparse
import os
import sys

import google.generativeai as genai
from google.api_core import exceptions


def setup_gemini(api_key):
    """Configures the Gemini API."""
    if not api_key:
        print("Error: GOOGLE_API_KEY environment variable not set.", file=sys.stderr)
        sys.exit(1)
    genai.configure(api_key=api_key)


def get_model(model_name="gemini-1.5-flash"):
    """Instantiates the generative model."""
    generation_config = {
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 8192,
    }
    return genai.GenerativeModel(
        model_name=model_name,
        generation_config=generation_config,
    )


def read_input(args):
    """Reads input from arguments or stdin pipe."""
    # If arguments are provided, join them as the prompt
    if args.prompt:
        return " ".join(args.prompt)

    # If no arguments, check if data is being piped into stdin
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()

    return None


def main():
    parser = argparse.ArgumentParser(description="CLI for Google Gemini")
    parser.add_argument("prompt", nargs="*", help="The prompt to send to Gemini")
    parser.add_argument("--model", default="gemini-1.5-flash", help="Model version to use")
    args = parser.parse_args()

    api_key = os.environ.get("GOOGLE_API_KEY")
    setup_gemini(api_key)

    user_input = read_input(args)

    if not user_input:
        print("Usage: python3 gemini_cli.py [PROMPT] or echo [PROMPT] | python3 gemini_cli.py")
        sys.exit(1)

    model = get_model(args.model)

    try:
        # Stream the response for a better CLI feel
        response = model.generate_content(user_input, stream=True)
        for chunk in response:
            print(chunk.text, end="", flush=True)
        print()  # Newline at the end
    except exceptions.GoogleAPICallError as e:
        print(f"\nAPI Error: {e}", file=sys.stderr)
    except Exception as e:
        print(f"\nUnexpected Error: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
