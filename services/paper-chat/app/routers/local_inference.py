"""
Local model inference router - routes requests to appropriate locally trained models.
Returns Server-Sent Events (SSE) stream for streaming responses.
"""
import asyncio
import logging
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.services.model_registry import get_status, is_local_available, get

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatRequest(BaseModel):
    mode: str
    message: str
    context: str | None = None


@router.get("/health")
async def health_check():
    """
    Frontend calls this to check if local models are available.
    Returns: { available: bool, models: { model_name: { loaded, version, description } } }
    """
    return {
        "available": is_local_available(),
        "models": get_status(),
    }


@router.post("/chat")
async def local_chat(request: ChatRequest):
    """
    Routes user message to appropriate local model(s).
    Returns a Server-Sent Events (SSE) stream.
    """
    async def generate():
        try:
            response_text = await _route_to_model(
                mode=request.mode,
                message=request.message,
                context=request.context,
            )

            # Stream word-by-word for natural feel
            words = response_text.split(" ")
            for i, word in enumerate(words):
                chunk = word + (" " if i < len(words) - 1 else "")
                yield f"data: {chunk}\n\n"
                await asyncio.sleep(0.02)

            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"Local inference error: {e}")
            yield f"data: ⚠️ Local model error: {str(e)}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def _route_to_model(mode: str, message: str, context: str | None) -> str:
    """
    Dispatches to the right local model based on chat mode and question content.
    Falls back to RAG engine for unhandled cases.
    """
    msg = message.lower()

    # GENERAL mode
    if mode == "general":
        return await _rag_query(message, context)

    # INTEGRITY (Module 1)
    elif mode == "integrity":
        if any(w in msg for w in ["citation", "reference", "apa", "ieee", "format"]):
            return await _citation_answer(message, context)
        elif any(w in msg for w in ["gap", "missing", "novel", "contribution", "unexplored"]):
            return await _gap_analysis(message, context)
        elif any(w in msg for w in ["summarize", "summary", "abstract"]):
            return await _summarize(context or message)
        elif any(w in msg for w in ["plagiarism", "similarity", "overlap"]):
            return await _plagiarism_check(message, context)
        else:
            return await _rag_query(message, context)

    # COLLABORATION (Module 2)
    elif mode == "collaboration":
        return await _supervisor_guidance(message, context)

    # DATA MANAGEMENT (Module 3)
    elif mode == "dataManagement":
        if any(w in msg for w in ["summarize", "summary"]):
            return await _summarize(context or message)
        elif any(w in msg for w in ["topic", "category", "classify"]):
            return await _topic_classification(message, context)
        else:
            return await _rag_query(message, context)

    # ANALYTICS (Module 4)
    elif mode == "analytics":
        if any(w in msg for w in ["trend", "forecast", "future", "predict"]):
            return await _trend_interpretation(message, context)
        elif any(w in msg for w in ["quality", "score", "improve"]):
            return await _quality_explanation(message, context)
        elif any(w in msg for w in ["risk", "success", "fail", "complete"]):
            return await _prediction_explanation(message, context)
        else:
            return await _rag_query(message, context)

    return (
        "I couldn't find a local model suitable for this question. "
        "Try switching to Gemini mode for general questions."
    )


# ─── Model-specific handlers ───────────────────────────────────────────

async def _rag_query(question: str, context: str | None) -> str:
    """Query the RAG engine."""
    rag = get("rag_engine")
    if not rag:
        return "RAG engine not ready. Please ensure papers are uploaded and indexed."
    try:
        if hasattr(rag, "query"):
            return await rag.query(question, extra_context=context)
        else:
            return f"I couldn't find relevant information in your papers about: {question}"
    except Exception as e:
        logger.error(f"RAG query error: {e}")
        return f"RAG engine error: {str(e)}"


async def _citation_answer(question: str, context: str | None) -> str:
    """Answer citation-related questions."""
    ner = get("citation_ner")
    if not ner:
        return "Citation NER model not trained yet. Train the model to enable citation parsing."
    try:
        if hasattr(ner, "answer_question"):
            return await ner.answer_question(question, context)
        else:
            return f"Based on citation NER, I can help with: {question}"
    except Exception as e:
        logger.error(f"Citation NER error: {e}")
        return f"Citation analysis error: {str(e)}"


async def _gap_analysis(question: str, context: str | None) -> str:
    """Perform gap analysis."""
    rag = get("rag_engine")
    if not rag:
        return "Gap analysis requires the RAG engine. Not ready yet."
    try:
        if hasattr(rag, "analyze_gaps"):
            return await rag.analyze_gaps(question, context)
        else:
            return f"Gap analysis for: {question}"
    except Exception as e:
        logger.error(f"Gap analysis error: {e}")
        return f"Gap analysis error: {str(e)}"


async def _summarize(text: str) -> str:
    """Summarize text."""
    summarizer = get("summarizer")
    if not summarizer:
        return "Summarizer model not trained yet. Train BART model to enable summarization."
    try:
        if hasattr(summarizer, "summarize"):
            return await summarizer.summarize(text[:4000])
        else:
            return f"Summary: {text[:500]}..."
    except Exception as e:
        logger.error(f"Summarizer error: {e}")
        return f"Summarization error: {str(e)}"


async def _plagiarism_check(question: str, context: str | None) -> str:
    """Check for plagiarism/similarity."""
    rag = get("rag_engine")
    if not rag:
        return "Plagiarism analysis requires the RAG engine. Not ready yet."
    try:
        if hasattr(rag, "check_similarity"):
            return await rag.check_similarity(question, context)
        else:
            return f"Plagiarism check for: {question}"
    except Exception as e:
        logger.error(f"Plagiarism check error: {e}")
        return f"Plagiarism check error: {str(e)}"


async def _supervisor_guidance(question: str, context: str | None) -> str:
    """Provide supervisor-style guidance."""
    rag = get("rag_engine")
    if not rag:
        return "Supervisor guidance requires the RAG engine. Not ready yet."
    try:
        if hasattr(rag, "supervisor_style_query"):
            return await rag.supervisor_style_query(question, context)
        else:
            return f"Supervisor guidance: {question}"
    except Exception as e:
        logger.error(f"Supervisor guidance error: {e}")
        return f"Supervisor guidance error: {str(e)}"


async def _topic_classification(question: str, context: str | None) -> str:
    """Classify text into topics."""
    classifier = get("scibert_classifier")
    if not classifier:
        return "Topic classifier (SciBERT) not trained yet. Train to enable categorization."
    try:
        if hasattr(classifier, "classify"):
            topics = await classifier.classify(context or question)
            if isinstance(topics, list):
                return f"Identified topics: {', '.join(topics)}"
            else:
                return str(topics)
        else:
            return "Topic classification available."
    except Exception as e:
        logger.error(f"Classifier error: {e}")
        return f"Classification error: {str(e)}"


async def _trend_interpretation(question: str, context: str | None) -> str:
    """Interpret trends."""
    forecaster = get("trend_forecaster")
    if not forecaster:
        return "Trend forecaster (ARIMA + Prophet) not trained yet."
    try:
        if hasattr(forecaster, "interpret"):
            return await forecaster.interpret(question, context)
        else:
            return f"Trend interpretation: {question}"
    except Exception as e:
        logger.error(f"Trend forecaster error: {e}")
        return f"Trend interpretation error: {str(e)}"


async def _quality_explanation(question: str, context: str | None) -> str:
    """Explain quality scores."""
    scorer = get("quality_scorer")
    if not scorer:
        return "Quality scorer not trained yet. Train to enable quality analysis."
    try:
        if hasattr(scorer, "explain"):
            return await scorer.explain(question, context)
        else:
            return f"Quality explanation: {question}"
    except Exception as e:
        logger.error(f"Quality scorer error: {e}")
        return f"Quality explanation error: {str(e)}"


async def _prediction_explanation(question: str, context: str | None) -> str:
    """Explain predictions."""
    predictor = get("success_predictor")
    if not predictor:
        return "Success predictor (XGBoost) not trained yet."
    try:
        if hasattr(predictor, "explain"):
            return await predictor.explain(question, context)
        else:
            return f"Prediction explanation: {question}"
    except Exception as e:
        logger.error(f"Predictor error: {e}")
        return f"Prediction explanation error: {str(e)}"
