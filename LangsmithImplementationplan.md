# LangSmith Integration Plan for Agentic AI Coding Assistant

## 1. Executive Summary

**Yes, absolutely!** LangSmith is designed specifically for this architecture. 

Because this project is built on **LangGraph** (`langgraph`) and **LangChain** (`langchain-openai`), native LangSmith tracing is already built into the underlying libraries. In fact, `langsmith` is already installed as a dependency inside the project environment.

Integrating LangSmith will provide:
- **Full Graph Visualization**: Step-by-step trace of the state machine (`planner` → `coder` → `reviewer` → `fixer`).
- **Structured Output Inspection**: Visibility into LLM schema outputs (`Plan`, `Step`, `ReviewList`, `Review`).
- **Loop & Retry Monitoring**: Visual comparison of codebase changes across retry cycles in the self-healing loop.
- **Cost, Latency, & Token Tracking**: Per-node and total execution metrics for OpenAI `gpt-4o`.
- **Debugging & Error Tracing**: Instant visibility into malformed responses, parse errors, or LLM refusals.

---

## 2. Integration Levels

We recommend a 3-tiered integration approach:

```
┌────────────────────────────────────────────────────────┐
│ Level 1: Zero-Code Tracing (Environment Variables)     │ ◄── Ready in 2 minutes
├────────────────────────────────────────────────────────┤
│ Level 2: Run Config, Metadata, & Tags (main.py)        │ ◄── Better search & filtering
├────────────────────────────────────────────────────────┤
│ Level 3: Custom Spans & File I/O Tracing (nodes.py)    │ ◄── Complete end-to-end audit
└────────────────────────────────────────────────────────┘
```

---

## 3. Step-by-Step Implementation Roadmap

### Phase 1: Environment & Dependency Setup

#### 1.1 Obtain LangSmith API Key
1. Sign in or create a free account at [smith.langchain.com](https://smith.langchain.com/).
2. Navigate to **Settings** → **API Keys** and click **Create API Key**.
3. Copy the key (starts with `lsv2_pt_...`).

#### 1.2 Update `.env.example`
Add the standard LangSmith configuration variables to `.env.example`:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# LangSmith Observability Configuration
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT="https://api.smith.langchain.com"
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_PROJECT="aiagent-coding-assistant"
```

#### 1.3 Update Active `.env`
Add your real `LANGSMITH_API_KEY` and project name into `.env`.

#### 1.4 Update `requirements.txt`
Explicitly pin `langsmith` in `requirements.txt` to guarantee reproducible installs:

```text
langgraph>=0.2.0
langchain-openai>=0.2.0
langsmith>=0.1.0
pydantic>=2.0.0
python-dotenv>=1.0.0
```

---

### Phase 2: Zero-Code Base Tracing (Instant Activation)

Since `main.py` calls `load_dotenv()` at line 6 *before* importing LangGraph components:

```python
# main.py
from dotenv import load_dotenv
load_dotenv()  # Reads LANGSMITH_TRACING, LANGSMITH_API_KEY, etc.
```

LangChain and LangGraph automatically detect these environment variables upon invocation. When `app.invoke({"task": task})` runs, every node transition and LLM call is immediately streamed to your LangSmith project dashboard.

---

### Phase 3: Enhanced Run Metadata & Tagging (`main.py`)

To make traces easily searchable in the LangSmith UI (e.g., filtering by model or task), enhance the invocation call in `main.py` with run configuration:

```python
# main.py (Updated main function)
def main():
    task = input("What would you like me to build?\n> ").strip()
    if not task:
        print("No task provided. Exiting.")
        return

    app = build_graph()

    # Pass LangSmith runtime configuration
    config = {
        "run_name": f"coding_task_{task[:30]}",
        "tags": ["cli", "agentic-coder", "gpt-4o"],
        "metadata": {
            "task_prompt": task,
            "version": "0.1.0",
        }
    }

    app.invoke({"task": task}, config=config)
```

---

### Phase 4: Custom Operation Tracing (`nodes.py`)

LangGraph automatically traces the `planner`, `coder`, `reviewer`, and `fixer` nodes, as well as all LLM calls. However, file system operations (writing files, creating directories, reading the codebase) happen in native Python.

Using LangSmith's `@traceable` decorator, we can turn these operations into visible child spans in the trace tree:

```python
# src/aiagent_coding_assistant/nodes.py
from langsmith import traceable

@traceable(name="write_file_to_disk", run_type="tool")
def write_file(path: str, content: str):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

@traceable(name="read_codebase", run_type="tool")
def load_codebase(files: list[str]) -> str:
    return "\n".join(f"--- {f} ---\n{open(f, encoding='utf-8').read()}" for f in files)
```

Then call these functions inside `coder`, `reviewer`, and `fixer`:
- You will see exactly when files are written to disk.
- You can inspect the exact codebase text passed to the reviewer directly in the trace viewer.

---

### Phase 5: Feedback & Evaluation Datasets (Optional / Advanced)

1. **Prompt Datasets**: Collect challenging user coding tasks directly from LangSmith production traces and click **"Add to Dataset"** to create a test suite.
2. **Automated Evaluators**: Create offline benchmark runs to evaluate code generation accuracy, cyclomatic complexity, or unit test pass rates across different models (e.g. `gpt-4o` vs `claude-3-5-sonnet` vs `gemini-2.0`).

---

## 4. Verification & Testing Checklist

| Step | Action | Expected Result |
| :--- | :--- | :--- |
| **1. Configuration** | Add `LANGSMITH_*` keys to `.env` | Environment variables loaded via `load_dotenv()` |
| **2. Test Execution** | Run `python main.py` with prompt: `"Create a hello world function in hello.py"` | Execution completes with standard console outputs |
| **3. UI Verification** | Open [smith.langchain.com](https://smith.langchain.com/) → project `aiagent-coding-assistant` | New run appears with name `coding_task_...` |
| **4. Hierarchy Check** | Expand the run tree in LangSmith | Shows tree: `LangGraph` → `planner` → `coder` → `reviewer` |
| **5. Metrics Check** | Inspect run details panel | Token count, latency, and estimated cost are populated |

---

## 5. Summary of Files to Modify

| File | Changes Required |
| :--- | :--- |
| [`.env.example`](file:///d:/IITPatna/AIAgent-coding_assistant/.env.example) | Add `LANGSMITH_TRACING`, `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT` |
| [`.env`](file:///d:/IITPatna/AIAgent-coding_assistant/.env) | Add personal LangSmith API credentials |
| [`requirements.txt`](file:///d:/IITPatna/AIAgent-coding_assistant/requirements.txt) | Add `langsmith>=0.1.0` |
| [`main.py`](file:///d:/IITPatna/AIAgent-coding_assistant/main.py) | Pass `config` dictionary with tags & metadata into `app.invoke()` |
| [`src/aiagent_coding_assistant/nodes.py`](file:///d:/IITPatna/AIAgent-coding_assistant/src/aiagent_coding_assistant/nodes.py) | (Optional) Add `@traceable` to file I/O operations |
| [`README.md`](file:///d:/IITPatna/AIAgent-coding_assistant/README.md) | Document LangSmith tracing setup and dashboard viewing |

