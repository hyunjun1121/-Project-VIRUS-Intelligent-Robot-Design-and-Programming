from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from eval_next_backend.models import Benchmark, Llm, Question, AnswerMeta
from eval_next_backend.dependencies import get_db
from ..api_types.benchmarks import BenchmarkMetadataResponse, BenchmarkResponse, BenchmarkTableRow, BenchmarkModelMeta, BenchmarkMeta, LlmMeta
from eval_next_backend.utils import group_by

router = APIRouter(
    prefix="/api/benchmarks",
    tags=["benchmarks"],
    responses={404: {"description": "Not found"}},
)

@router.get("/metadata", response_model=BenchmarkMetadataResponse)
async def get_benchmark_metadata(db: Session = Depends(get_db)):
    benchmarks = [
        BenchmarkMeta(id=str(b.id), name=b.name, description=b.description)
        for b in db.query(Benchmark).all()
    ]
    llms = [
        LlmMeta(id=str(m.id), name=m.name)
        for m in db.query(Llm).all()
    ]
    return {"benchmarks": benchmarks, "llms": llms}

@router.get("/{benchmark_id}", response_model=BenchmarkResponse)
async def get_benchmark_data(
    benchmark_id: str,
    offset: int = Query(0, ge=0, description="Offset for infinite loading"),
    limit: int = Query(20, ge=1, le=100, description="Number of items to load"),
    db: Session = Depends(get_db)
):
    questions = (
        db.query(Question)
        .filter(Question.benchmark_id == int(benchmark_id))
        .order_by(Question.id)
        .offset(offset)
        .limit(limit)
        .all()
    )
    question_ids = [q.id for q in questions]

    answer_metas = db.query(AnswerMeta).filter(AnswerMeta.question_id.in_(question_ids)).all()
    answer_metas_of_question = group_by(answer_metas, lambda am: am.question_id)

    table_rows = []
    for q in questions:
        answer_metas = answer_metas_of_question.get(q.id, {})
        table_rows.append(BenchmarkTableRow(
            id=q.id,
            question=q.prompt,
            difficulty=q.difficulty,
            model_metas={str(am.llm_id): BenchmarkModelMeta(score=am.score) for am in answer_metas}
        ))

    return BenchmarkResponse(table_rows=table_rows) 