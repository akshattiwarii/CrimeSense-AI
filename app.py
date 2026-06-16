import argparse
import json
import os
import sys

from crimesense_ai.analyzer import analyze_complaint
from crimesense_ai.config import load_dotenv
from crimesense_ai.server import run


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="CrimeSense AI complaint triage")
    parser.add_argument("--serve", action="store_true", help="Run the web app")
    parser.add_argument("--host", default="127.0.0.1", help="Server host")
    parser.add_argument("--port", default=int(os.getenv("PORT", "8000")), type=int, help="Server port")
    parser.add_argument("--text", help="Analyze complaint text from command line")
    args = parser.parse_args()

    if args.serve:
        run(args.host, args.port)
        return

    complaint_text = args.text or sys.stdin.read()
    result = analyze_complaint(complaint_text)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
