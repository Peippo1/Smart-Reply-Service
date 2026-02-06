import logging

from fastapi import APIRouter, Depends

from app.api.schemas import DraftRequest, DraftResponse, HealthResponse
from app.middleware.rate_limit import rate_limit_dependency
from app.services.llm import generate_reply_drafts
from app.auth import require_api_key

router = APIRouter(tags=["reply"], responses={429: {"description": "Rate limit exceeded"}})
logger = logging.getLogger(__name__)



@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.post(
    "/v1/reply/draft",
    response_model=DraftResponse,
    dependencies=[Depends(require_api_key)],
    summary="Generate three channel-appropriate reply drafts",
    description=(
        "Generates three reply drafts tailored to the specified channel (email, Slack, LinkedIn). "
        "Applies channel-specific formatting rules (greeting/sign-off for email, bullets/length for Slack, "
        "short paragraphs and soft CTA for LinkedIn) and honours constraints like max words, must-include-question, "
        "and avoid phrases. Defaults to UK English spelling unless overridden via options."
    ),
)
async def create_reply_draft(
    request: DraftRequest, rate_limit=Depends(rate_limit_dependency)
) -> DraftResponse:
    # Dependency order ensures auth and rate-limit are applied before draft generation.
    response = generate_reply_drafts(request)
    logger.info(
        "drafts.generated",
        extra={
            "request_id": response.request_id,
            "channel": response.channel_applied,
            "detected_tone": response.detected_tone,
        },
    )
    return response
