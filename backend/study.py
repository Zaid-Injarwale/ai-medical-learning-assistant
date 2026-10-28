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
# STUDY RESPONSE STRUCTURE
# ============================================================

class StudyResponse(BaseModel):
    topic: str
    difficulty: Literal["basic", "intermediate", "advanced"]

    introduction: str

    key_concepts: list[str] = Field(
        description="Important concepts the student should understand."
    )

    detailed_explanation: str

    clinical_relevance: str

    exam_points: list[str] = Field(
        description="Important points useful for medical examinations."
    )

    memory_aid: str


# ============================================================
# GENERATE STUDY LESSON
# ============================================================

def generate_study_lesson(
    topic: str,
    difficulty: str = "basic"
) -> StudyResponse:

    topic = topic.strip()

    if not topic:
        raise RuntimeError("Please enter a medical topic.")

    prompt = f"""
You are an expert medical education AI.

Teach a medical student about the following topic:

Topic:
{topic}

Difficulty:
{difficulty}

Create a clear educational lesson.

Requirements:

1. Start with a simple introduction.
2. Explain the most important concepts.
3. Give a detailed but understandable explanation.
4. Keep the explanation focused on the requested topic.
5. Include clinically relevant information suitable for a medical student.
6. Include important examination points.
7. Give a useful memory aid or mnemonic when appropriate.
8. Use medically accurate educational information.
9. Do not provide personal medical diagnosis or treatment advice.
10. Adjust the depth according to the selected difficulty.
"""

    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": StudyResponse,
                "thinking_config": {
                    "thinking_level": "low"
                },
            },
        )

        result = response.parsed

        if result is None:
            raise RuntimeError("Gemini returned an empty study lesson.")

        return result

    except Exception as e:
        raise RuntimeError(
            f"Study lesson generation failed: {str(e)}"
        )