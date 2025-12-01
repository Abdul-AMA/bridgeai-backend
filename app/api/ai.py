from fastapi import APIRouter
from app.ai.state import AgentState
from app.ai.nodes.echo_node import echo_node
from app.ai.graph import create_graph

router = APIRouter()

graph = create_graph()

@router.post("/echo")
def echo(state: AgentState):
    result = graph.invoke(state)
    return result

