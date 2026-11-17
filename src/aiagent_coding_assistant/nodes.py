import os
from langchain_openai import ChatOpenAI
from .state import State, Plan, ReviewList

llm = ChatOpenAI(model="gpt-4o", temperature=0)

def planner(state: State):
    plan = llm.with_structured_output(Plan).invoke(
        f"Break this coding task into file-by-file steps:\n{state['task']}"
    )
    return {"steps": [s.model_dump() for s in plan.steps], "files": [], "retries": 0}

def coder(state: State):
    step = state["steps"].pop(0)
    path = step["file_path"]
    print(f"Writing {path}...")

    code = llm.invoke(
        f"Task: {state['task']}\nWrite ONLY raw code (no markdown backticks) for {path}: {step['instruction']}"
    ).content.strip("` \n")

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        f.write(code)

    return {"steps": state["steps"], "files": state["files"] + [path]}

def reviewer(state: State):
    print("Reviewing files...")
    codebase = "\n".join(f"--- {f} ---\n{open(f).read()}" for f in state["files"])
    
    report = llm.with_structured_output(ReviewList).invoke(
        f"Review these files for bugs or missing logic against the task: {state['task']}\n\n{codebase}"
    )
    failed = [r.model_dump() for r in report.reviews if not r.passed]
    return {"failed": failed}

def fixer(state: State):
    for item in state["failed"]:
        path = item["file_path"]
        print(f"Fixing {path}...")
        
        fixed_code = llm.invoke(
            f"Fix {path} based on this feedback: {item['feedback']}\nReturn ONLY raw code:\n{open(path).read()}"
        ).content.strip("` \n")
        
        with open(path, "w") as f:
            f.write(fixed_code)

    return {"retries": state["retries"] + 1}