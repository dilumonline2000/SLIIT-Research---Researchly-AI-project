from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from uuid import UUID
from datetime import datetime


# --- Papers ---
class ProcessRequest(BaseModel):
    paper_id: UUID


class PaperOut(BaseModel):
    id: UUID
    title: Optional[str] = None
    authors: Optional[List[str]] = None
    abstract: Optional[str] = None
    page_count: Optional[int] = None
    processing_status: str
    created_at: Optional[datetime] = None


class TrainingDataOut(BaseModel):
    paper_id: UUID
    version: str = "1.0"
    extracted_at: datetime
    data: Dict[str, Any]


# --- Chat ---
class CreateSessionRequest(BaseModel):
    title: Optional[str] = None
    paper_ids: List[UUID] = Field(default_factory=list)
    session_type: str = "paper_specific"
    preferred_language: str = "auto"
    module_context: Optional[str] = None


class SessionOut(BaseModel):
    id: UUID
    title: Optional[str] = None
    session_type: str
    paper_ids: List[UUID] = Field(default_factory=list)
    preferred_language: str
    message_count: int = 0
    created_at: Optional[datetime] = None


class SendMessageRequest(BaseModel):
    content: str
    language_override: Optional[str] = None


class ChatMessageOut(BaseModel):
    id: UUID
    role: str
    content: str
    detected_language: Optional[str] = None
    citations: Optional[List[Dict[str, Any]]] = None
    created_at: Optional[datetime] = None


class FeedbackRequest(BaseModel):
    message_id: UUID
    rating: Optional[int] = None
    is_helpful: Optional[bool] = None
    feedback_text: Optional[str] = None


# --- Language ---
class DetectRequest(BaseModel):
    text: str


class DetectResponse(BaseModel):
    language: str
    confidence: float = 1.0
    is_singlish: bool = False


class TranslateRequest(BaseModel):
    text: str
    source: str = "auto"
    target: str = "en"


class TranslateResponse(BaseModel):
    translated: str
    source: str
    target: str


# --- Training ---
class TrainingStatus(BaseModel):
    pending: int
    queued: int
    completed: int
    failed: int
    by_model: Dict[str, int]


class ModelVersionOut(BaseModel):
    id: UUID
    model_name: str
    version: str
    is_active: bool
    metrics: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
