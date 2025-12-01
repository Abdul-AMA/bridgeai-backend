from typing import TypedDict, Optional

class AgentState(TypedDict, total=False):
    user_input: str
    output: Optional[str]
