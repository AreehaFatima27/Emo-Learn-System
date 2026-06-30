import os
import json
from mistralai.client import Mistral
from dotenv import load_dotenv

load_dotenv()

client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))
MODEL = "mistral-large-latest"


def generate_quiz(topic: str, num_questions: int) -> dict:
    """
    Calls Mistral API to generate a quiz.
    Returns: { complexity, questions: [{question, options, correct, explanation}] }
    """
    prompt = f"""You are an expert quiz generator. Generate exactly {num_questions} multiple-choice quiz questions about the topic: "{topic}".

Your generated questions must follow a strict difficulty curve:
- The first 30% of the questions must be beginner/basic level.
- The middle 40% of the questions must be intermediate level.
- The final 30% of the questions must be advanced/complex level.
Ensure the questions are strictly ordered from easiest (question 1) to hardest (last question).

Automatically assess the topic depth and assign a complexity level.

Return ONLY valid JSON, no markdown, no extra text. Format:
{{
  "complexity": "beginner" | "intermediate" | "expert",
  "questions": [
    {{
      "question": "Full question text here?",
      "options": {{
        "A": "Option A text",
        "B": "Option B text",
        "C": "Option C text",
        "D": "Option D text"
      }},
      "correct": "A" | "B" | "C" | "D",
      "explanation": "Brief explanation of why this answer is correct."
    }}
  ]
}}

Rules:
- Questions must be clear and unambiguous
- Distractors (wrong options) must be plausible
- Cover different aspects of the topic
- Explanations should be educational and concise (1-2 sentences)
- Ensure a clear and smooth progression in difficulty from basic to complex concepts."""

    response = client.chat.complete(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a quiz generation expert. Always return valid JSON only."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=4000
    )

    raw = response.choices[0].message.content.strip()

    # Strip markdown code block if present
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1])

    return json.loads(raw)
