from typing import List, Dict
from pydantic import BaseModel

class BenchmarkMeta(BaseModel):
    id: str
    name: str
    description: str

class BenchmarkOptionsResponse(BaseModel):
    benchmarks: List[BenchmarkMeta]

class LlmMeta(BaseModel):
    id: str
    name: str

class BenchmarkMetadataResponse(BaseModel):
    benchmarks: List[BenchmarkMeta]
    llms: List[LlmMeta]

class BenchmarkModelMeta(BaseModel):
    score: float

class BenchmarkTableRow(BaseModel):
    id: int
    question: str
    difficulty: float
    model_metas: Dict[str, BenchmarkModelMeta]

class BenchmarkResponse(BaseModel):
    table_rows: List[BenchmarkTableRow] 