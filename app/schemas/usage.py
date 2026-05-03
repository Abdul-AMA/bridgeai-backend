from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel


class AIUsageLogResponse(BaseModel):
    id: int
    user_id: int
    project_id: Optional[int]
    session_id: Optional[int]
    node_type: str
    model_name: str
    provider: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    created_at: datetime

    class Config:
        from_attributes = True


class NodeTypeStats(BaseModel):
    calls: int
    tokens: int


class DailyStats(BaseModel):
    date: str
    calls: int
    input_tokens: int
    output_tokens: int


class AIUsageSummaryResponse(BaseModel):
    total_calls: int
    total_input_tokens: int
    total_output_tokens: int
    total_tokens: int
    by_node_type: Dict[str, NodeTypeStats]
    daily_breakdown: List[DailyStats]
    estimated_cost_usd: float


class AIUsageHistoryResponse(BaseModel):
    total: int
    page: int
    limit: int
    items: List[AIUsageLogResponse]
