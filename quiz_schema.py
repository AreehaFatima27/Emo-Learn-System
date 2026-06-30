from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid


class QuizGenerateRequest(BaseModel):
    topic: str
    num_questions: int = 10  # 5 | 10 | 15


class OptionSet(BaseModel):
    A: str
    B: str
    C: str
    D: str


class QuestionOut(BaseModel):
    question_id: uuid.UUID
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    question_order: int

    model_config = {"from_attributes": True}


class QuizSessionOut(BaseModel):
    session_id: uuid.UUID
    topic: str
    complexity: str
    num_questions: int
    status: str
    started_at: datetime
    questions: List[QuestionOut]

    model_config = {"from_attributes": True}


class AnswerSubmit(BaseModel):
    question_id: uuid.UUID
    user_answer: Optional[str] = None  # A | B | C | D | None
    time_taken: Optional[int] = None   # in seconds


class QuizSubmitRequest(BaseModel):
    session_id: uuid.UUID
    answers: List[AnswerSubmit]


class QuestionResult(BaseModel):
    question_id: uuid.UUID
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    user_answer: Optional[str]
    correct_answer: str
    is_correct: bool
    explanation: Optional[str]
    question_order: int

    model_config = {"from_attributes": True}


class QuizResultOut(BaseModel):
    session_id: uuid.UUID
    topic: str
    complexity: str
    score: int
    total_marks: int
    percentage: float
    results: List[QuestionResult]

    model_config = {"from_attributes": True}


class SessionSummary(BaseModel):
    session_id: uuid.UUID
    topic: str
    complexity: str
    score: Optional[int]
    total_marks: Optional[int]
    status: str
    started_at: datetime
    completed_at: Optional[datetime]

    model_config = {"from_attributes": True}
