import sys
from pathlib import Path
from dotenv import load_dotenv

# 1. Load .env variables FIRST
load_dotenv()

# 2. Add 'src' to Python's search path (needed if package isn't installed via pip/uv)
sys.path.append(str(Path(__file__).parent / "src"))

# 3. Import from your renamed package
from aiagent_coding_assistant.graph import build_graph

def main():
    task = input("What would you like me to build?\n> ").strip()
    if not task:
        print("No task provided. Exiting.")
        return

    app = build_graph()
    app.invoke({"task": task})

if __name__ == "__main__":
    main()