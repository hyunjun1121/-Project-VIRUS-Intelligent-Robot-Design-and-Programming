from sqlalchemy import Column, Integer, String, Float, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# TODO add index etc
class Benchmark(Base):
    __tablename__ = 'benchmarks'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    description = Column(String, nullable=False)

class Llm(Base):
    __tablename__ = 'llms'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    overall_score = Column(Float, nullable=False)
    category_scores = Column(JSON, nullable=False)

class Question(Base):
    __tablename__ = 'questions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    benchmark_id = Column(Integer, nullable=False)
    prompt = Column(String, nullable=False)
    difficulty = Column(Float, nullable=False)

class AnswerMeta(Base):
    __tablename__ = 'answer_metas'
    id = Column(Integer, primary_key=True, autoincrement=True)
    question_id = Column(Integer, nullable=False)
    llm_id = Column(Integer, nullable=False)
    score = Column(Float, nullable=False)

class Conversation(Base):
    __tablename__ = 'conversations'
    id = Column(Integer, primary_key=True, autoincrement=True)
    question_id = Column(Integer, nullable=False)
    llm_id = Column(Integer, nullable=False)
    attempt_index = Column(Integer, nullable=False)
    score = Column(Float, nullable=False)
    messages = Column(JSON, nullable=False) 