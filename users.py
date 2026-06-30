from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database.connection import get_db
from database.models import User, QuizSession, SentimentLog, EmotionLog
from schemas.user_schema import UserOut, UserUpdate
from routes.auth import get_current_user
from collections import Counter
import json

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sessions = db.query(QuizSession).filter(
        QuizSession.user_id == current_user.user_id,
        QuizSession.status == "completed"
    ).order_by(QuizSession.completed_at.desc()).all()

    total_quizzes = len(sessions)
    avg_score = 0.0
    score_history = []

    if sessions:
        scored = [s for s in sessions if s.score is not None and s.total_marks]
        if scored:
            avg_score = round(sum((s.score / s.total_marks) * 100 for s in scored) / len(scored), 1)
        score_history = [
            {
                "session_id": str(s.session_id),
                "topic": s.topic,
                "score": s.score,
                "total": s.total_marks,
                "percentage": round((s.score / s.total_marks) * 100, 1) if s.total_marks else 0,
                "date": s.completed_at.isoformat() if s.completed_at else s.started_at.isoformat()
            }
            for s in sessions[:20]
        ]

    # Sentiment / emotion trend (last 30 days)
    sentiment_logs = db.query(SentimentLog).filter(
        SentimentLog.user_id == current_user.user_id
    ).order_by(SentimentLog.created_at.desc()).limit(10).all()

    sentiment_history = [
        {
            "topic": s.topic,
            "sentiment": s.sentiment,
            "grip_level": s.grip_level,
            "score": s.sentiment_score,
            "date": s.created_at.isoformat()
        }
        for s in sentiment_logs
    ]

    # Dominant emotion from webcam data
    emotion_logs = db.query(EmotionLog).filter(
        EmotionLog.user_id == current_user.user_id
    ).limit(200).all()
    emotion_counts = dict(Counter(l.emotion for l in emotion_logs if l.emotion))
    dominant_emotion = max(emotion_counts, key=emotion_counts.get) if emotion_counts else "neutral"

    # Recent sessions (last 5)
    recent = [
        {
            "session_id": str(s.session_id),
            "topic": s.topic,
            "complexity": s.complexity,
            "score": s.score,
            "total": s.total_marks,
            "date": s.completed_at.isoformat() if s.completed_at else s.started_at.isoformat()
        }
        for s in sessions[:5]
    ]

    return {
        "total_quizzes": total_quizzes,
        "avg_score_percent": avg_score,
        "dominant_emotion": dominant_emotion,
        "emotion_counts": emotion_counts,
        "score_history": score_history,
        "sentiment_history": sentiment_history,
        "recent_sessions": recent
    }


@router.put("/profile", response_model=UserOut)
def update_profile(payload: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if payload.full_name:
        current_user.full_name = payload.full_name
    if payload.avatar_url is not None:
        current_user.avatar_url = payload.avatar_url
    db.commit()
    db.refresh(current_user)
    return UserOut.model_validate(current_user)
