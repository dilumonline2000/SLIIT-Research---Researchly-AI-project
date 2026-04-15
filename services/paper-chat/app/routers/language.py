"""Language detection + translation endpoints."""

from fastapi import APIRouter

from ..schemas import DetectRequest, DetectResponse, TranslateRequest, TranslateResponse
from ..services.language_service import detect_language, translate

router = APIRouter()


@router.post("/detect", response_model=DetectResponse)
async def detect(req: DetectRequest) -> DetectResponse:
    lang, conf, is_singlish = detect_language(req.text)
    return DetectResponse(language=lang, confidence=conf, is_singlish=is_singlish)


@router.post("/translate", response_model=TranslateResponse)
async def translate_endpoint(req: TranslateRequest) -> TranslateResponse:
    out = translate(req.text, source=req.source, target=req.target)
    return TranslateResponse(translated=out, source=req.source, target=req.target)
