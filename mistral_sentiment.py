import os
import json
from mistralai.client import Mistral
from dotenv import load_dotenv

load_dotenv()

client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))
MODEL = "mistral-large-latest"


def analyze_sentiment(
    topic: str,
    score: int,
    total: int,
    num_questions: int,
    questions_detail: list[dict],
    duration_seconds: int,
    emotion_summary: dict | None = None,
    avg_response_time: float | None = None,
) -> dict:
    """
    Calls Mistral API to analyze the student's quiz performance and generate
    deep sentiment + learning insight, incorporating emotion and timing data.

    Returns: {
      sentiment, sentiment_score, grip_level,
      analysis_text, concepts_to_master, recommendation
    }
    """
    percentage = round((score / total) * 100) if total > 0 else 0
    minutes = duration_seconds // 60
    seconds = duration_seconds % 60

    # Build question details breakdown
    detail_lines = []
    for q in questions_detail:
        correct_status = "Correct" if q["is_correct"] else "Incorrect"
        emotions_str = ", ".join(set(q["detected_emotions"])) if q["detected_emotions"] else "no webcam readings"
        detail_lines.append(
            f"  - Question {q['question_order']}: \"{q['question_text']}\" | Status: {correct_status} | Time Taken: {q['time_taken_seconds']}s | Emotions: {emotions_str}"
        )
    questions_detail_str = "\n".join(detail_lines)

    # Build emotion context
    emotion_context = ""
    if emotion_summary and emotion_summary.get("emotion_counts"):
        dom = emotion_summary.get("dominant_emotion", "neutral")
        counts = emotion_summary.get("emotion_counts", {})
        total_readings = sum(counts.values()) or 1
        emotion_lines = [
            f"  - {e}: {round(v/total_readings*100)}%" for e, v in sorted(counts.items(), key=lambda x: -x[1])
        ]
        emotion_context = f"""
WEBCAM EMOTION TRACKING OVERALL:
- Dominant emotion during quiz: {dom}
- Emotion breakdown:
{chr(10).join(emotion_lines)}
"""

    # Build timing context
    timing_context = ""
    if avg_response_time is not None:
        if avg_response_time < 10:
            timing_hint = "answered very quickly (high confidence or guessing)"
        elif avg_response_time < 25:
            timing_hint = "answered at a thoughtful pace (good engagement)"
        elif avg_response_time < 45:
            timing_hint = "took significant time (careful thinking or uncertainty)"
        else:
            timing_hint = "took very long per question (possible confusion or deep thinking)"
        timing_context = f"""
RESPONSE TIMING OVERALL:
- Average time per question: {avg_response_time:.1f} seconds
- Behavioral pattern: {timing_hint}
"""

    prompt = f"""You are an expert learning psychologist and education analyst. A student just completed an adaptive quiz.

QUIZ DETAILS:
- Topic: "{topic}"
- Score: {score} out of {total} ({percentage}%)
- Number of Questions: {num_questions}
- Time Taken: {minutes}m {seconds}s
{timing_context}
QUESTION-BY-QUESTION LOG (Ordered from easiest/basic to hardest/advanced):
{questions_detail_str}

{emotion_context}

ANALYSIS TASK:
Perform a holistic analysis of this student's understanding of "{topic}".
Consider carefully:
1. The quiz questions strictly progressed from basic (first 30%), to intermediate (middle 40%), to advanced/complex (final 30%).
2. Analyze how their response times and emotional states changed as complexity increased.
   - E.g., if they answered basic questions quickly and correctly with neutral/happy emotions, but took very long (or got incorrect answers) with confused/frustrated emotions on advanced questions, they have a solid grip on basics but struggle with advanced concepts.
   - If they rushed through all questions very quickly (< 8s each) and got many wrong, they likely guessed.
3. Provide an encouraging, growth-mindset assessment based on these observations.

Return ONLY valid JSON, no markdown, no extra text:
{{
  "sentiment": "confident" | "confused" | "frustrated" | "mastery" | "neutral",
  "sentiment_score": <float between -1.0 (very negative) and 1.0 (very positive)>,
  "grip_level": "weak" | "developing" | "solid" | "strong" | "expert",
  "analysis_text": "<3-5 sentences personalized analysis explaining their performance, how their emotions/timings changed as questions became more complex, and what this implies about their grip on the concepts>",
  "concepts_to_master": [
    "<specific concept 1 they need to study>",
    "<specific concept 2 they need to study>",
    "<specific concept 3 they need to study>"
  ],
  "recommendation": "<2-3 sentences concrete next-step advice, recommending specific actions or study topics based on their grip profile>"
}}

Rules:
- Be encouraging even for low scores — focus on growth mindset
- concepts_to_master should be SPECIFIC sub-topics of "{topic}", not generic advice
- If score >= 80%, grip_level should be "strong" or "expert"
- If score < 40%, grip_level should be "weak" or "developing"
- If they failed mostly the advanced questions, highlight that their "grip" is solid on the basics but developing/weak on advanced parts
- sentiment_score must be a decimal number"""

    response = client.chat.complete(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are an expert learning psychologist. Always return valid JSON only."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.6,
        max_tokens=1800
    )

    raw = response.choices[0].message.content.strip()

    # Strip markdown code block if present
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1])

    return json.loads(raw)
