from fastapi import APIRouter, Depends

from app.api.schemas import DraftRequest, DraftResponse, HealthResponse
from app.middleware.auth import verify_api_key
from app.middleware.rate_limit import rate_limit_dependency
from app.services.llm import generate_drafts

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.post(
    "/v1/reply/draft",
    response_model=DraftResponse,
    dependencies=[Depends(verify_api_key)],
)
async def create_reply_draft(
    request: DraftRequest, rate_limit=Depends(rate_limit_dependency())
) -> DraftResponse:
    drafts = list(generate_drafts(request))
    return DraftResponse(
        drafts=drafts,
        channel=request.channel,
        requested_tone=request.tone,
        evidence="Confidence is heuristic based on tone/channel fit.",
    )

