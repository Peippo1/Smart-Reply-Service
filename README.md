# Smart Reply Service

FastAPI microservice that generates three channel-appropriate reply drafts with tone labels and simple confidence heuristics.

## Quickstart

Requirements: Python 3.11+, `pip`.

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` for interactive API docs.

## Endpoints

- `GET /health` — basic liveness probe.
- `POST /v1/reply/draft` — generate three reply drafts. Example body:

```json
{
  "message": "Can you share the latest metrics for Q1?",
  "context": "Thread with finance leadership",
  "channel": "email",
  "tone": "professional",
  "constraints": {
    "word_limit": 80,
    "must_include_question": true,
    "avoid_phrases": ["ASAP"]
  }
}
```

## Docker

```bash
docker build -t smart-reply-service .
docker run -p 8000:8000 smart-reply-service
```

