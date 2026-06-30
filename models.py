import uuid
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text,
    DateTime, ForeignKey, CheckConstraint, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.connection import Base


# ─────────────────────────────────────────────
# 1. USERS
# ─────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    password_hash = Column(Text, nullable=False)
    role = Column(String(20), default="student")  # 'student' | 'admin'
    avatar_url = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    quiz_sessions = relationship("QuizSession", back_populates="user", cascade="all, delete")
    sentiment_logs = relationship("SentimentLog", back_populates="user", cascade="all, delete")
    emotion_logs = relationship("EmotionLog", back_populates="user", cascade="all, delete")
    enrollments = relationship("Enrollment", back_populates="user", cascade="all, delete")
    recommendations = relationship("Recommendation", back_populates="user", cascade="all, delete")


# ─────────────────────────────────────────────
# 2. QUIZ SESSIONS
# ─────────────────────────────────────────────
class QuizSession(Base):
    __tablename__ = "quiz_sessions"

    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    topic = Column(String(255), nullable=False)
    complexity = Column(String(50), default="auto")  # beginner | intermediate | expert | auto
    num_questions = Column(Integer, default=10)
    total_marks = Column(Integer, nullable=True)
    score = Column(Integer, nullable=True)
    status = Column(String(20), default="in_progress")  # in_progress | completed
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="quiz_sessions")
    questions = relationship("QuizQuestion", back_populates="session", cascade="all, delete")
    answers = relationship("UserAnswer", back_populates="session", cascade="all, delete")
    sentiment_logs = relationship("SentimentLog", back_populates="session", cascade="all, delete")
    emotion_logs = relationship("EmotionLog", back_populates="session", cascade="all, delete")


# ─────────────────────────────────────────────
# 3. QUIZ QUESTIONS
# ─────────────────────────────────────────────
class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    question_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("quiz_sessions.session_id", ondelete="CASCADE"), nullable=False)
    question_text = Column(Text, nullable=False)
    option_a = Column(Text, nullable=False)
    option_b = Column(Text, nullable=False)
    option_c = Column(Text, nullable=False)
    option_d = Column(Text, nullable=False)
    correct_answer = Column(String(1), nullable=False)  # A | B | C | D
    explanation = Column(Text, nullable=True)
    question_order = Column(Integer, nullable=False)

    # Relationships
    session = relationship("QuizSession", back_populates="questions")
    answers = relationship("UserAnswer", back_populates="question", cascade="all, delete")


# ─────────────────────────────────────────────
# 4. USER ANSWERS
# ─────────────────────────────────────────────
class UserAnswer(Base):
    __tablename__ = "user_answers"

    answer_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("quiz_sessions.session_id", ondelete="CASCADE"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("quiz_questions.question_id", ondelete="CASCADE"), nullable=False)
    user_answer = Column(String(1), nullable=True)  # A | B | C | D | None (skipped)
    is_correct = Column(Boolean, nullable=True)
    time_taken = Column(Integer, nullable=True)     # Time taken in seconds
    answered_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session = relationship("QuizSession", back_populates="answers")
    question = relationship("QuizQuestion", back_populates="answers")


# ─────────────────────────────────────────────
# 5. SENTIMENT LOGS ⭐ Active Phase 1
# ─────────────────────────────────────────────
class SentimentLog(Base):
    __tablename__ = "sentiment_logs"

    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey("quiz_sessions.session_id", ondelete="CASCADE"), nullable=True)
    topic = Column(String(255), nullable=True)
    sentiment = Column(String(50), nullable=True)  # confident | confused | frustrated | mastery | neutral
    sentiment_score = Column(Float, nullable=True)  # -1.0 to 1.0
    grip_level = Column(String(50), nullable=True)  # weak | developing | solid | strong | expert
    analysis_text = Column(Text, nullable=True)     # Full AI analysis
    concepts_to_master = Column(Text, nullable=True)  # JSON array of concept strings
    recommendation = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="sentiment_logs")
    session = relationship("QuizSession", back_populates="sentiment_logs")


# ─────────────────────────────────────────────
# 6. EMOTION LOGS ⭐ Active Phase 1 (MediaPipe)
# ─────────────────────────────────────────────
class EmotionLog(Base):
    __tablename__ = "emotion_logs"

    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey("quiz_sessions.session_id", ondelete="CASCADE"), nullable=True)
    question_index = Column(Integer, nullable=True)  # which question was being shown
    emotion = Column(String(50), nullable=True)  # happy | neutral | sad | confused | surprised | frustrated
    confidence = Column(Float, nullable=True)    # 0.0 to 1.0
    blendshape_data = Column(Text, nullable=True)  # JSON of raw blendshape scores
    logged_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="emotion_logs")
    session = relationship("QuizSession", back_populates="emotion_logs")


# ─────────────────────────────────────────────
# 7. COURSES (Schema Only — Coming Soon)
# ─────────────────────────────────────────────
class Course(Base):
    __tablename__ = "courses"

    course_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    materials = relationship("Material", back_populates="course", cascade="all, delete")
    enrollments = relationship("Enrollment", back_populates="course", cascade="all, delete")
    recommendations = relationship("Recommendation", back_populates="material")


# ─────────────────────────────────────────────
# 8. MATERIALS (Schema Only — Coming Soon)
# ─────────────────────────────────────────────
class Material(Base):
    __tablename__ = "materials"

    material_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.course_id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    content_url = Column(Text, nullable=True)
    material_type = Column(String(50), nullable=True)  # video | pdf | article | link
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    course = relationship("Course", back_populates="materials")


# ─────────────────────────────────────────────
# 9. ENROLLMENTS (Schema Only — Coming Soon)
# ─────────────────────────────────────────────
class Enrollment(Base):
    __tablename__ = "enrollments"

    enrollment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.course_id", ondelete="CASCADE"), nullable=False)
    enrolled_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("user_id", "course_id", name="uq_enrollment"),)

    user = relationship("User", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")


# ─────────────────────────────────────────────
# 10. RECOMMENDATIONS (Schema Only — Coming Soon)
# ─────────────────────────────────────────────
class Recommendation(Base):
    __tablename__ = "recommendations"

    rec_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    material_id = Column(UUID(as_uuid=True), ForeignKey("courses.course_id"), nullable=True)
    reason = Column(Text, nullable=True)
    emotion_trigger = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="recommendations")
    material = relationship("Course", back_populates="recommendations")
