from typing import List
from pydantic import BaseModel

class Message(BaseModel):
    role: str
    content: str

class QuestionAttemptAnswer(BaseModel):
    index: int
    score: float
    messages: List[Message]

class QuestionLlmAnswer(BaseModel):
    llm_id: str
    llm_name: str
    attempts: List[QuestionAttemptAnswer]

class QuestionResponse(BaseModel):
    id: str
    difficulty: float
    benchmark_category: str
    question: str
    llm_answers: List[QuestionLlmAnswer] 