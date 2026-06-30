from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid


class SentimentOut(BaseModel):
    log_id: uuid.UUID
    session_id: Optional[uuid.UUID]
    topic: Optional[str]
    sentiment: Optional[str]
    sentiment_score: Optional[float]
    grip_level: Optional[str]
    analysis_text: Optional[str]
    concepts_to_master: Optional[List[str]]
    recommendation: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class EmotionBatchItem(BaseModel):
    question_index: int
    emotion: str
    confidence: float
    blendshape_data: Optional[str] = None  # JSON string of raw blendshapes


class EmotionBatchRequest(BaseModel):
    session_id: uuid.UUID
    readings: List[EmotionBatchItem]


class EmotionSummary(BaseModel):
    session_id: uuid.UUID
    dominant_emotion: str
    emotion_counts: dict
    average_confidence: float
