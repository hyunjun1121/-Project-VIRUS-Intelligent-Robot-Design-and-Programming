from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import questions, benchmarks, leaderboard

app = FastAPI(title="Eval Next Backend", version="1.0.0")

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://127.0.0.1:3001"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(questions.router)
app.include_router(benchmarks.router)
app.include_router(leaderboard.router)


@app.get("/")
async def root():
    return {"message": "Hello from Eval Next Backend!"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"} 