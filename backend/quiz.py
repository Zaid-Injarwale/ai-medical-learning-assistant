import os
from typing import Literal

from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel, Field


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY is missing")

client = genai.Client(api_key=API_KEY)


# ============================================================
# QUIZ RESPONSE STRUCTURE
# ============================================================

class QuizQuestion(BaseModel):
    question: str
    options: list[str] = Field(
        description="Exactly 4 answer options in A, B, C, D order."
    )
    correct_answer: Literal["A", "B", "C", "D"]
    explanation: str


class MedicalQuizResponse(BaseModel):
    topic: str
    difficulty: Literal["basic", "intermediate", "advanced"]
    questions: list[QuizQuestion]


# ============================================================
# GENERATE MEDICAL QUIZ
# ============================================================

def generate_medical_quiz(
    topic: str,
    difficulty: str = "basic"
) -> MedicalQuizResponse:

    topic = topic.strip()

    if not topic:
        raise RuntimeError("Please enter a medical topic.")

    prompt = f"""
You are an expert medical education AI.

Create a medical quiz for a medical student.

Topic:
{topic}

Difficulty:
{difficulty}

Requirements:
1. Generate exactly 5 multiple-choice questions.
2. Each question must have exactly 4 options.
3. Options must be in A, B, C, D order.
4. Only one option must be correct.
5. correct_answer must contain only A, B, C, or D.
6. Give a short educational explanation for the correct answer.
7. Questions must stay focused on the requested topic.
8. Do not ask diagnosis or personal medical-treatment questions.
9. Use medically accurate educational information.
10. Do not include the correct answer inside the question text.
"""

    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": MedicalQuizResponse,
                "thinking_config": {
                    "thinking_level": "low"
                },
            },
        )

        result = response.parsed

        if result is None:
            raise RuntimeError("Gemini returned an empty quiz.")

        if len(result.questions) != 5:
            raise RuntimeError(
                f"Gemini returned {len(result.questions)} questions instead of 5."
            )

        for question in result.questions:
            if len(question.options) != 4:
                raise RuntimeError(
                    "A quiz question did not contain exactly 4 options."
                )

        return result

    except Exception as e:
        raise RuntimeError(
            f"Quiz generation failed: {str(e)}"
        )