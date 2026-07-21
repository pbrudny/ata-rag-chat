import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse

from app.db.session import get_db
from app.schemas.chat import ChatRequest
from app.services.chat_service import stream_chat_response

router = APIRouter()


def _format_sse(event: str, data) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("")
async def chat(request: ChatRequest, db: Session = Depends(get_db)) -> StreamingResponse:
    async def event_stream() -> AsyncIterator[str]:
        async for item in stream_chat_response(db, request.question, top_k=request.top_k):
            yield _format_sse(item["event"], item["data"])

    return StreamingResponse(event_stream(), media_type="text/event-stream")
