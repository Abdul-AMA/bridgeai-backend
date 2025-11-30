from langgraph.graph import StateGraph, END
from app.ai.state import AgentState
from app.ai.nodes.echo_node import echo_node

def create_graph():
    graph = StateGraph(AgentState)

    graph.add_node("echo", echo_node)
    graph.set_entry_point("echo")
    graph.add_edge("echo", END)

    return graph.compile()