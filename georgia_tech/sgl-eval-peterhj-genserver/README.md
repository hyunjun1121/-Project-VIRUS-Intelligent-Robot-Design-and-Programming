# sgl-eval

## Development Guide

### Setup

#### Install dependencies

```bash
uv sync
```

#### Generate data

```bash
uv run python eval_next_backend/data_source/fake_data_generator.py
```

### Run

#### Backend

The server will be available at http://127.0.0.1:8000

```bash
uv run uvicorn eval_next_backend.main:app --reload
```

#### Frontend

The frontend will be available at http://127.0.0.1:3001

```bash
PORT=3001 npm run dev
```

### API Documentation

- Interactive API docs: http://127.0.0.1:8000/docs
- Alternative API docs: http://127.0.0.1:8000/redoc
