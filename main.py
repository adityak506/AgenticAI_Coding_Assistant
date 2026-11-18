import sys
import pprint
from pathlib import Path
from dotenv import load_dotenv

# 1. Load .env variables FIRST (LangSmith tracing requires variables to be loaded before runnables execute)
load_dotenv()

# 2. Add 'src' to Python's search path (needed if package isn't installed via pip/uv)
sys.path.append(str(Path(__file__).parent / "src"))

# 3. Import from your package
from aiagent_coding_assistant.graph import build_graph

def main():
    task = input("What would you like me to build?\n> ").strip()
    if not task:
        print("No task provided. Exiting.")
        return

    app = build_graph()

    # Configure LangSmith run tracking, tags, and metadata
    config = {
        "run_name": f"task_{task[:30]}",
        "tags": ["coding-assistant", "cli"],
        "metadata": {
            "task_prompt": task,
            "version": "0.1.0"
        }
    }

    final_state = app.invoke({"task": task}, config=config)

    print("\n" + "#" * 60)
    print("🎉 [WORKFLOW COMPLETE] Final Accumulated State:")
    print("#" * 60)
    pprint.pprint(final_state, indent=2)
    print("#" * 60 + "\n")

if __name__ == "__main__":
    main()
