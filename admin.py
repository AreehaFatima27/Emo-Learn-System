from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database.connection import get_db
from database.models import User, QuizSession
from schemas.user_schema import UserOut
from routes.auth import require_admin
from typing import List

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users", response_model=List[UserOut])
def list_users(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    users = db.query(User).order_by(User.created_at.desc()).all()
    return [UserOut.model_validate(u) for u in users]


@router.get("/sessions")
def list_sessions(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    sessions = db.query(QuizSession).order_by(QuizSession.started_at.desc()).limit(100).all()

    # Build a user lookup for display names
    user_ids = list(set(str(s.user_id) for s in sessions))
    users = db.query(User).filter(User.user_id.in_([s.user_id for s in sessions])).all()
    user_map = {str(u.user_id): u.full_name for u in users}

    return [
        {
            "session_id": str(s.session_id),
            "user_id": str(s.user_id),
            "user_name": user_map.get(str(s.user_id), "Unknown"),
            "topic": s.topic,
            "complexity": s.complexity,
            "score": s.score,
            "total_marks": s.total_marks,
            "status": s.status,
            "started_at": s.started_at.isoformat() if s.started_at else None,
            "completed_at": s.completed_at.isoformat() if s.completed_at else None
        }
        for s in sessions
    ]


@router.get("/stats")
def admin_stats(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    total_users = db.query(User).count()
    total_sessions = db.query(QuizSession).count()
    completed_sessions = db.query(QuizSession).filter(QuizSession.status == "completed").count()

    # Calculate platform-wide average score percentage
    avg_score = None
    if completed_sessions > 0:
        completed = db.query(QuizSession).filter(
            QuizSession.status == "completed",
            QuizSession.score.isnot(None),
            QuizSession.total_marks > 0
        ).all()
        if completed:
            percentages = [(s.score / s.total_marks * 100) for s in completed if s.total_marks > 0]
            avg_score = round(sum(percentages) / len(percentages), 1) if percentages else None

    return {
        "total_users": total_users,
        "total_sessions": total_sessions,
        "completed_sessions": completed_sessions,
        "avg_score": avg_score
    }
