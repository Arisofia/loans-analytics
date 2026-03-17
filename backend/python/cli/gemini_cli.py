import argparse
import os
import sys

import google.genai as genai
from google.genai import types


def setup_gemini(api_key):
    """Create and return Gemini client."""
    if not api_key:
        print("Error: GOOGLE_API_KEY environment variable not set.", file=sys.stderr)
        sys.exit(1)
    return genai.Client(api_key=api_key)


def get_generation_config():
    """Build generation config for CLI calls."""
    return types.GenerateContentConfig(
        temperature=0.7,
        top_p=0.95,
        top_k=64,
        max_output_tokens=8192,
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
    client = setup_gemini(api_key)

    user_input = read_input(args)

    if not user_input:
        print("Usage: python3 gemini_cli.py [PROMPT] or echo [PROMPT] | python3 gemini_cli.py")
        sys.exit(1)

    generation_config = get_generation_config()

    try:
        # Stream the response for a better CLI feel
        stream = client.models.generate_content_stream(
            model=args.model,
            contents=user_input,
            config=generation_config,
        )
        for chunk in stream:
            chunk_text = getattr(chunk, "text", "")
            if chunk_text:
                print(chunk_text, end="", flush=True)
        print()  # Newline at the end
    except Exception as e:
        print(f"\nUnexpected Error: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
