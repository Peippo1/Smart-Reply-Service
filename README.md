# Smart Reply Service

FastAPI microservice that generates three channel-appropriate reply drafts with tone labels and simple confidence heuristics.

## Quickstart

Requirements: Python 3.11+, `pip`.

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` for interactive API docs.

### Example requests

Email:
```bash
curl -X POST http://localhost:8000/v1/reply/draft \
  -H "Content-Type: application/json" \
  -d '{"incoming_message":"Could you share the Q1 metrics?","channel":"email","tone":"professional"}'
```

Slack:
```bash
curl -X POST http://localhost:8000/v1/reply/draft \
  -H "Content-Type: application/json" \
  -d '{"incoming_message":"Can someone review the PR today?","channel":"slack","tone":"concise","options":{"emoji":true}}'
```

LinkedIn:
```bash
curl -X POST http://localhost:8000/v1/reply/draft \
  -H "Content-Type: application/json" \
  -d '{"incoming_message":"Enjoyed your post on data platforms—open to connecting?","channel":"linkedin","tone":"polite"}'
```

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
