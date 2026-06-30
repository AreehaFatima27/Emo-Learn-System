from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from database.connection import get_db
from database.models import User, QuizSession, QuizQuestion, UserAnswer
from schemas.quiz_schema import (
    QuizGenerateRequest, QuizSessionOut, QuizSubmitRequest,
    QuizResultOut, QuestionResult, SessionSummary
)
from services.mistral_quiz import generate_quiz
from routes.auth import get_current_user
from typing import List
import uuid

router = APIRouter(prefix="/quiz", tags=["Quiz"])


@router.post("/generate", response_model=QuizSessionOut)
def generate(payload: QuizGenerateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if payload.num_questions not in [5, 10, 15]:
        raise HTTPException(status_code=400, detail="num_questions must be 5, 10, or 15")

    try:
        quiz_data = generate_quiz(payload.topic, payload.num_questions)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI quiz generation failed: {str(e)}")

    # Create session
    session = QuizSession(
        user_id=current_user.user_id,
        topic=payload.topic,
        complexity=quiz_data.get("complexity", "auto"),
        num_questions=payload.num_questions,
        total_marks=payload.num_questions,
        status="in_progress"
    )
    db.add(session)
    db.flush()

    # Store questions
    for idx, q in enumerate(quiz_data.get("questions", [])):
        opts = q.get("options", {})
        question = QuizQuestion(
            session_id=session.session_id,
            question_text=q["question"],
            option_a=opts.get("A", ""),
            option_b=opts.get("B", ""),
            option_c=opts.get("C", ""),
            option_d=opts.get("D", ""),
            correct_answer=q.get("correct", "A"),
            explanation=q.get("explanation", ""),
            question_order=idx + 1
        )
        db.add(question)

    db.commit()
    db.refresh(session)
    return QuizSessionOut.model_validate(session)


@router.post("/submit", response_model=QuizResultOut)
def submit(payload: QuizSubmitRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(QuizSession).filter(
        QuizSession.session_id == payload.session_id,
        QuizSession.user_id == current_user.user_id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Quiz session not found")
    if session.status == "completed":
        raise HTTPException(status_code=400, detail="Quiz already submitted")

    questions = {str(q.question_id): q for q in session.questions}
    score = 0
    results = []

    for ans in payload.answers:
        q = questions.get(str(ans.question_id))
        if not q:
            continue
        is_correct = ans.user_answer == q.correct_answer if ans.user_answer else False
        if is_correct:
            score += 1

        user_answer_obj = UserAnswer(
            session_id=session.session_id,
            question_id=q.question_id,
            user_answer=ans.user_answer,
            is_correct=is_correct,
            time_taken=ans.time_taken
        )
        db.add(user_answer_obj)

        results.append(QuestionResult(
            question_id=q.question_id,
            question_text=q.question_text,
            option_a=q.option_a,
            option_b=q.option_b,
            option_c=q.option_c,
            option_d=q.option_d,
            user_answer=ans.user_answer,
            correct_answer=q.correct_answer,
            is_correct=is_correct,
            explanation=q.explanation,
            question_order=q.question_order
        ))

    session.score = score
    session.status = "completed"
    session.completed_at = datetime.now(timezone.utc)
    db.commit()

    results.sort(key=lambda r: r.question_order)
    percentage = round((score / session.total_marks) * 100, 1) if session.total_marks else 0

    return QuizResultOut(
        session_id=session.session_id,
        topic=session.topic,
        complexity=session.complexity,
        score=score,
        total_marks=session.total_marks,
        percentage=percentage,
        results=results
    )


@router.get("/sessions", response_model=List[SessionSummary])
def get_sessions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sessions = db.query(QuizSession).filter(
        QuizSession.user_id == current_user.user_id
    ).order_by(QuizSession.started_at.desc()).all()
    return [SessionSummary.model_validate(s) for s in sessions]


@router.get("/sessions/{session_id}", response_model=QuizResultOut)
def get_session(session_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(QuizSession).filter(
        QuizSession.session_id == session_id,
        QuizSession.user_id == current_user.user_id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    results = []
    for ans in session.answers:
        q = ans.question
        results.append(QuestionResult(
            question_id=q.question_id,
            question_text=q.question_text,
            option_a=q.option_a,
            option_b=q.option_b,
            option_c=q.option_c,
            option_d=q.option_d,
            user_answer=ans.user_answer,
            correct_answer=q.correct_answer,
            is_correct=ans.is_correct or False,
            explanation=q.explanation,
            question_order=q.question_order
        ))
    results.sort(key=lambda r: r.question_order)
    percentage = round((session.score / session.total_marks) * 100, 1) if session.total_marks and session.score is not None else 0

    return QuizResultOut(
        session_id=session.session_id,
        topic=session.topic,
        complexity=session.complexity,
        score=session.score or 0,
        total_marks=session.total_marks or 0,
        percentage=percentage,
        results=results
    )
