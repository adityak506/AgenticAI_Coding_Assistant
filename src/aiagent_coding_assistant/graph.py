from langgraph.graph import StateGraph, START, END
from .state import State
from .nodes import planner, coder, reviewer, fixer

def build_graph():
    graph = StateGraph(State)

    graph.add_node("planner", planner)
    graph.add_node("coder", coder)
    graph.add_node("reviewer", reviewer)
    graph.add_node("fixer", fixer)

    graph.add_edge(START, "planner")
    graph.add_edge("planner", "coder")
    graph.add_conditional_edges("coder", lambda s: "coder" if s["steps"] else "reviewer")
    graph.add_conditional_edges(
        "reviewer", 
        lambda s: "fixer" if s["failed"] and s["retries"] < 2 else END
    )
    graph.add_edge("fixer", "reviewer")

    return graph.compile()