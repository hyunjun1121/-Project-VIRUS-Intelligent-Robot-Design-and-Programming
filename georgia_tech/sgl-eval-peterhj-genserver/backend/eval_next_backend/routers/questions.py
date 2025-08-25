from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as SessionType
from eval_next_backend.models import Question, Conversation, Llm, Benchmark
from eval_next_backend.dependencies import get_db
from ..api_types.questions import QuestionResponse, QuestionLlmAnswer, QuestionAttemptAnswer, Message
from collections import defaultdict
from eval_next_backend.utils import group_by

router = APIRouter(
    prefix="/api/questions",
    tags=["questions"],
    responses={404: {"description": "Not found"}},
)

@router.get("/{question_id}", response_model=QuestionResponse)
async def get_question(question_id: str, db: SessionType = Depends(get_db)):
    question = db.query(Question).filter(Question.id == int(question_id)).first()
    if not question:
        return None

    benchmark = db.query(Benchmark).filter(Benchmark.id == question.benchmark_id).first()
    benchmark_category = benchmark.category if benchmark else ""

    conversations = db.query(Conversation).filter(Conversation.question_id == int(question_id)).all()
    conversation_map = group_by(conversations, lambda c: c.llm_id)

    llm_ids = {c.llm_id for c in conversations}
    llm_names = {llm.id: llm.name for llm in db.query(Llm).filter(Llm.id.in_(llm_ids))}

    llm_answers = [
        QuestionLlmAnswer(
            llm_id=str(llm_id),
            llm_name=llm_names[llm_id],
            attempts=[
                QuestionAttemptAnswer(
                    index=conv.attempt_index,
                    score=conv.score,
                    messages=[Message(**msg) for msg in conv.messages]
                )
                for conv in sorted(attempts, key=lambda x: x.attempt_index)
            ]
        )
        for llm_id, attempts in conversation_map.items()
    ]

    return QuestionResponse(
        id=str(question.id),
        difficulty=question.difficulty,
        benchmark_category=benchmark_category,
        question=question.prompt,
        llm_answers=llm_answers
    ) 