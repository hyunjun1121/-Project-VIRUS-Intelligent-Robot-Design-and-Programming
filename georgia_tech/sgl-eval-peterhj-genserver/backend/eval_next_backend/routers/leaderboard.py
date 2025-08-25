from eval_next_backend.consts import CATEGORY_NAMES
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as SessionType
from eval_next_backend.models import Llm
from eval_next_backend.dependencies import get_db
from ..api_types.leaderboard import LeaderboardResponse

router = APIRouter(
    prefix="/api/leaderboard",
    tags=["leaderboard"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=LeaderboardResponse)
async def get_leaderboard(db: SessionType = Depends(get_db)):
    llms = db.query(Llm).all()
    llms = sorted(llms, key=lambda x: x.overall_score, reverse=True)

    table_rows = []
    for i, llm in enumerate(llms):
        table_rows.append({
            "rank": i + 1,
            "llm_name": llm.name,
            "overall_score": llm.overall_score,
            "category_scores": llm.category_scores,
        })

    return {
        "category_names": CATEGORY_NAMES,
        "table_rows": table_rows
    } 