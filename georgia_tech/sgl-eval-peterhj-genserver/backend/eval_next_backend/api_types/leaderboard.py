from typing import List, Dict
from pydantic import BaseModel

class LeaderboardTableRow(BaseModel):
    rank: int
    llm_name: str
    overall_score: float
    category_scores: Dict[str, float]

class LeaderboardResponse(BaseModel):
    category_names: List[str]
    table_rows: List[LeaderboardTableRow] 