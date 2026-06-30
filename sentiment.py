from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models import User, QuizSession, QuizQuestion, UserAnswer, SentimentLog, EmotionLog
from schemas.sentiment_schema import SentimentOut, EmotionBatchRequest, EmotionSummary
from services.mistral_sentiment import analyze_sentiment
from routes.auth import get_current_user
from typing import List
from collections import Counter
import json, uuid

router = APIRouter(prefix="/sentiment", tags=["Sentiment"])


@router.post("/analyze", response_model=SentimentOut)
def analyze(session_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(QuizSession).filter(
        QuizSession.session_id == session_id,
        QuizSession.user_id == current_user.user_id,
        QuizSession.status == "completed"
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Completed quiz session not found")

    # Check if already analyzed
    existing = db.query(SentimentLog).filter(SentimentLog.session_id == session_id).first()
    if existing:
        concepts = json.loads(existing.concepts_to_master) if existing.concepts_to_master else []
        return SentimentOut(
            log_id=existing.log_id,
            session_id=existing.session_id,
            topic=existing.topic,
            sentiment=existing.sentiment,
            sentiment_score=existing.sentiment_score,
            grip_level=existing.grip_level,
            analysis_text=existing.analysis_text,
            concepts_to_master=concepts,
            recommendation=existing.recommendation,
            created_at=existing.created_at
        )

    # Build question details (including timing and corresponding emotions)
    duration = 0
    if session.started_at and session.completed_at:
        duration = int((session.completed_at - session.started_at).total_seconds())

    # Gather emotion data for this session
    emotion_logs = db.query(EmotionLog).filter(
        EmotionLog.session_id == session_id,
        EmotionLog.user_id == current_user.user_id
    ).all()

    questions_detail = []
    for ans in session.answers:
        q_order = ans.question.question_order if ans.question else 0
        q_text = ans.question.question_text if ans.question else "Unknown Question"
        # Match emotion logs with this question index (0-indexed question index matches q_order - 1)
        q_emotions = [l.emotion for l in emotion_logs if l.question_index == (q_order - 1) and l.emotion]
        
        questions_detail.append({
            "question_order": q_order,
            "question_text": q_text,
            "is_correct": ans.is_correct or False,
            "time_taken_seconds": ans.time_taken or 0,
            "detected_emotions": q_emotions
        })

    # Sort questions by order
    questions_detail.sort(key=lambda x: x["question_order"])

    emotion_summary = None
    if emotion_logs:
        emotions = [l.emotion for l in emotion_logs if l.emotion]
        counts = dict(Counter(emotions))
        dominant = max(counts, key=counts.get) if counts else "neutral"
        avg_conf = sum(l.confidence for l in emotion_logs if l.confidence) / len(emotion_logs) if emotion_logs else 0
        emotion_summary = {
            "dominant_emotion": dominant,
            "emotion_counts": counts,
            "average_confidence": round(avg_conf, 3)
        }

    # Calculate average response time per question from quiz duration
    avg_response_time = None
    if session.num_questions and session.num_questions > 0 and duration > 0:
        avg_response_time = duration / session.num_questions

    try:
        result = analyze_sentiment(
            topic=session.topic,
            score=session.score or 0,
            total=session.total_marks or session.num_questions,
            num_questions=session.num_questions,
            questions_detail=questions_detail,
            duration_seconds=duration,
            emotion_summary=emotion_summary,
            avg_response_time=avg_response_time,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Sentiment analysis failed: {str(e)}")

    concepts = result.get("concepts_to_master", [])
    log = SentimentLog(
        user_id=current_user.user_id,
        session_id=session.session_id,
        topic=session.topic,
        sentiment=result.get("sentiment", "neutral"),
        sentiment_score=result.get("sentiment_score", 0.0),
        grip_level=result.get("grip_level", "developing"),
        analysis_text=result.get("analysis_text", ""),
        concepts_to_master=json.dumps(concepts),
        recommendation=result.get("recommendation", "")
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    return SentimentOut(
        log_id=log.log_id,
        session_id=log.session_id,
        topic=log.topic,
        sentiment=log.sentiment,
        sentiment_score=log.sentiment_score,
        grip_level=log.grip_level,
        analysis_text=log.analysis_text,
        concepts_to_master=concepts,
        recommendation=log.recommendation,
        created_at=log.created_at
    )


@router.get("/analyze", response_model=SentimentOut)
def get_analysis(session_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """GET endpoint for retrieving existing analysis (used by results page)."""
    existing = db.query(SentimentLog).filter(SentimentLog.session_id == session_id).first()
    if not existing:
        # If no analysis exists yet, trigger one
        return analyze(session_id, db, current_user)
    concepts = json.loads(existing.concepts_to_master) if existing.concepts_to_master else []
    return SentimentOut(
        log_id=existing.log_id,
        session_id=existing.session_id,
        topic=existing.topic,
        sentiment=existing.sentiment,
        sentiment_score=existing.sentiment_score,
        grip_level=existing.grip_level,
        analysis_text=existing.analysis_text,
        concepts_to_master=concepts,
        recommendation=existing.recommendation,
        created_at=existing.created_at
    )


@router.get("/history", response_model=List[SentimentOut])
def history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    logs = db.query(SentimentLog).filter(
        SentimentLog.user_id == current_user.user_id
    ).order_by(SentimentLog.created_at.desc()).all()

    result = []
    for log in logs:
        concepts = json.loads(log.concepts_to_master) if log.concepts_to_master else []
        result.append(SentimentOut(
            log_id=log.log_id,
            session_id=log.session_id,
            topic=log.topic,
            sentiment=log.sentiment,
            sentiment_score=log.sentiment_score,
            grip_level=log.grip_level,
            analysis_text=log.analysis_text,
            concepts_to_master=concepts,
            recommendation=log.recommendation,
            created_at=log.created_at
        ))
    return result


router_emotions = APIRouter(prefix="/emotions", tags=["Emotions"])


@router_emotions.post("/log")
def log_emotions(payload: EmotionBatchRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    for reading in payload.readings:
        entry = EmotionLog(
            user_id=current_user.user_id,
            session_id=payload.session_id,
            question_index=reading.question_index,
            emotion=reading.emotion,
            confidence=reading.confidence,
            blendshape_data=reading.blendshape_data
        )
        db.add(entry)
    db.commit()
    return {"message": "Emotion batch logged", "count": len(payload.readings)}


@router_emotions.get("/summary/{session_id}", response_model=EmotionSummary)
def emotion_summary(session_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    logs = db.query(EmotionLog).filter(
        EmotionLog.session_id == session_id,
        EmotionLog.user_id == current_user.user_id
    ).all()

    if not logs:
        return EmotionSummary(
            session_id=session_id,
            dominant_emotion="neutral",
            emotion_counts={},
            average_confidence=0.0
        )

    emotions = [l.emotion for l in logs if l.emotion]
    counts = dict(Counter(emotions))
    dominant = max(counts, key=counts.get) if counts else "neutral"
    avg_conf = sum(l.confidence for l in logs if l.confidence) / len(logs)

    return EmotionSummary(
        session_id=session_id,
        dominant_emotion=dominant,
        emotion_counts=counts,
        average_confidence=round(avg_conf, 3)
    )
