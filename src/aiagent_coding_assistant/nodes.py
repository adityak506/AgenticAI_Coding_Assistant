import os
import pprint
from langchain_openai import ChatOpenAI
from langsmith import traceable
from .state import State, Plan, ReviewList

llm = ChatOpenAI(model="gpt-4o", temperature=0)

@traceable(name="write_file_to_disk", run_type="tool")
def write_file_to_disk(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

@traceable(name="read_file_from_disk", run_type="tool")
def read_file_from_disk(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

@traceable(name="read_codebase", run_type="tool")
def read_codebase(files: list[str]) -> str:
    return "\n".join(f"--- {f} ---\n{read_file_from_disk(f)}" for f in files)

def planner(state: State):
    print("\n" + "=" * 60)
    print("📋 [NODE: planner] Planning task into steps...")
    print("=" * 60)

    plan = llm.with_structured_output(Plan).invoke(
        f"Break this coding task into file-by-file steps:\n{state['task']}",
        config={"run_name": "planner_task_decomposition"}
    )
    steps = [s.model_dump() for s in plan.steps]

    print("\n--- Planner Generated Steps ---")
    for idx, s in enumerate(steps, 1):
        print(f"  Step {idx}: {s['file_path']}")
        print(f"          Instruction: {s['instruction']}")
    print("-" * 31 + "\n")

    output = {"steps": steps, "files": [], "retries": 0}
    print("[State Output after 'planner']:")
    pprint.pprint(output, indent=2)
    print("=" * 60 + "\n")
    return output

def coder(state: State):
    step = state["steps"].pop(0)
    path = step["file_path"]

    print("\n" + "=" * 60)
    print(f"💻 [NODE: coder] Generating code for: {path}")
    print(f"   Instruction: {step['instruction']}")
    print("=" * 60)

    code = llm.invoke(
        f"Task: {state['task']}\nWrite ONLY raw code (no markdown backticks) for {path}: {step['instruction']}",
        config={"run_name": f"coder_generate_code:{os.path.basename(path)}"}
    ).content.strip("` \n")

    write_file_to_disk(path, code)
    print(f"   Saved {path} to disk.")

    output = {"steps": state["steps"], "files": state["files"] + [path]}
    print("\n[State Output after 'coder']:")
    pprint.pprint(output, indent=2)
    print("=" * 60 + "\n")
    return output

def reviewer(state: State):
    print("\n" + "=" * 60)
    print(f"🔍 [NODE: reviewer] Reviewing files: {state['files']}")
    print("=" * 60)

    codebase = read_codebase(state["files"])
    
    report = llm.with_structured_output(ReviewList).invoke(
        f"Review these files for bugs or missing logic against the task: {state['task']}\n\n{codebase}",
        config={"run_name": "reviewer_codebase_evaluation"}
    )
    failed = [r.model_dump() for r in report.reviews if not r.passed]

    if failed:
        print(f"   ⚠️ Reviewer found {len(failed)} issue(s):")
        for item in failed:
            print(f"     - {item['file_path']}: {item['feedback']}")
    else:
        print("   ✅ All files passed review!")

    output = {"failed": failed}
    print("\n[State Output after 'reviewer']:")
    pprint.pprint(output, indent=2)
    print("=" * 60 + "\n")
    return output

def fixer(state: State):
    retry_count = state["retries"] + 1
    print("\n" + "=" * 60)
    print(f"🔧 [NODE: fixer] Fixing {len(state['failed'])} failed file(s) (Retry attempt {retry_count})")
    print("=" * 60)

    for item in state["failed"]:
        path = item["file_path"]
        print(f"   Fixing {path} based on feedback: {item['feedback']}...")
        
        current_code = read_file_from_disk(path)
        fixed_code = llm.invoke(
            f"Fix {path} based on this feedback: {item['feedback']}\nReturn ONLY raw code:\n{current_code}",
            config={"run_name": f"fixer_patch_code:{os.path.basename(path)}"}
        ).content.strip("` \n")
        
        write_file_to_disk(path, fixed_code)
        print(f"   Updated {path} on disk.")

    output = {"retries": retry_count}
    print("\n[State Output after 'fixer']:")
    pprint.pprint(output, indent=2)
    print("=" * 60 + "\n")
    return output
