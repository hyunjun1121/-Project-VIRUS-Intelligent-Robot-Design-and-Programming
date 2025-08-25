from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from eval_next_backend.models import Base, Benchmark, Llm, Question, AnswerMeta, Conversation
from eval_next_backend.consts import DB_PATH, DB_URL, CATEGORY_NAMES
import random

DB_PATH.parent.mkdir(parents=True, exist_ok=True)
DB_PATH.unlink(missing_ok=True)

engine = create_engine(DB_URL, echo=True)
Session = sessionmaker(bind=engine)
session = Session()

Base.metadata.create_all(engine)

llm_names = [
    "o3", "o4 mini", "Gemini 2.5 Pro", "Gemini 2.5 Flash",
    "Deepseek V3", "Deepseek R1", "Qwen 3 32B", "Qwen 3 8B", "Claude Sonnet 4"
]
llms = [
    Llm(
        name=name,
        overall_score=round(random.uniform(70, 100), 2),
        category_scores={cat: round(random.uniform(60, 100), 2) for cat in CATEGORY_NAMES}
    )
    for name in llm_names
]
session.add_all(llms)
session.commit()

benchmark_name_map = {
    "math": ["HMMT", "AIME 25", "AIME 24", "Math500"],
    "coding": ["SWE Bench Verified", "Aider", "MMAU Code", "Livecode Bench", "Livecode Bench Pro ?", "HumanEval", "terminalbench"],
    "knowledge": ["Humanity's last exam", "GPQA Diamond", "MMLU-Pro", "MMLU", "PHYBench", "SimpleQA"],
    "agent": ["NexusBench", "TauBench 2", "ToolSandbox", "BFCL V2/V3"],
}
benchmarks = []
for cat in CATEGORY_NAMES:
    for n in benchmark_name_map.get(cat, []):
        benchmarks.append(Benchmark(name=n, category=cat, description=f"Description for {n}"))
session.add_all(benchmarks)
session.commit()

questions = []
for b in benchmarks:
    for i in range(1, 51):
        questions.append(Question(
            benchmark_id=b.id,
            prompt=f"Prompt {i} for {b.name}",
            difficulty=round(random.uniform(0.1, 1.0), 2)
        ))
session.add_all(questions)
session.commit()

answer_metas = []
for q in questions:
    for llm in llms:
        answer_metas.append(AnswerMeta(
            question_id=q.id,
            llm_id=llm.id,
            score=random.choice([round(x * 0.2, 1) for x in range(6)])
        ))
session.add_all(answer_metas)
session.commit()

lorem_ipsum = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum. "

conversations = []
for q in questions:
    for llm in llms:
        for attempt in range(random.randint(1, 3)):
            messages = [
                {"role": "assistant", "content": f"Assistant message a for {llm.name} and attempt {attempt}. {lorem_ipsum * 5}"},
                {"role": "user", "content": f"User message a."},
                {"role": "assistant", "content": f"Assistant message b. {lorem_ipsum * 5}"},
            ]
            conversations.append(Conversation(
                question_id=q.id,
                llm_id=llm.id,
                attempt_index=attempt,
                score=round(random.uniform(0, 1), 2),
                messages=messages
            ))
session.add_all(conversations)
session.commit()

print('Fake data inserted into all tables.') 
