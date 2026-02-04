# Smart Reply Service

FastAPI microservice that generates three channel-appropriate reply drafts with tone labels and simple confidence heuristics.

## Quickstart

Requirements: Python 3.11+, `pip`.

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` for interactive API docs (public by default; consider restricting in prod).

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
- `POST /v1/reply/draft` — generate three reply drafts with channel-aware formatting, constraint enforcement, and confidence scoring. Example body:

```json
{
  "incoming_message": "Can you share the latest metrics for Q1?",
  "context": "Thread with finance leadership",
  "channel": "email",
  "tone": "professional",
  "constraints": {
    "max_words": 120,
    "must_include_question": true,
    "avoid_phrases": ["ASAP"]
  },
  "options": {
    "emoji": false,
    "uk_english": true
  }
}
```

Response shape:
```json
{
  "request_id": "string",
  "detected_tone": "neutral-professional",
  "channel_applied": "email",
  "drafts": [
    {"label": "Option 1", "text": "..." },
    {"label": "Option 2", "text": "..." },
    {"label": "Option 3", "text": "..." }
  ],
  "notes": "Applied channel formatting; enforced constraints.",
  "confidence_score": 0.0
}
```

### Auth & rate limiting
- API key is optional; set `SMART_REPLY_API_KEY` to require `x-api-key`.
- Rate limit defaults to 60 req/min per IP; override with `SMART_REPLY_RATE_LIMIT_PER_MINUTE`.

### OpenAI integration (future-ready)
- Stub drafts are generated locally. To switch to OpenAI later, set `SMART_REPLY_OPENAI_API_KEY` (and optional `SMART_REPLY_OPENAI_MODEL`, `SMART_REPLY_OPENAI_BASE_URL`). The pipeline is already wired for the Responses API.

## Docker

```bash
docker build -t smart-reply-service .
docker run -p 8000:8000 smart-reply-service
```
