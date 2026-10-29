from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Literal

from ai import ask_medical_ai
from study import generate_study_lesson
from quiz import generate_medical_quiz


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="AI Medical Learning Assistant"
)


# ============================================================
# CHAT MESSAGE
# ============================================================

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


# ============================================================
# QUESTION REQUEST
# ============================================================

class QuestionRequest(BaseModel):
    question: str
    history: list[ChatMessage] = Field(default_factory=list)


# ============================================================
# STUDY REQUEST
# ============================================================

class StudyRequest(BaseModel):
    topic: str
    difficulty: Literal[
        "basic",
        "intermediate",
        "advanced"
    ] = "basic"


# ============================================================
# QUIZ REQUEST
# ============================================================

class QuizRequest(BaseModel):
    topic: str
    difficulty: Literal[
        "basic",
        "intermediate",
        "advanced"
    ] = "basic"


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():
    return FileResponse("frontend/index.html")


# ============================================================
# ASK MEDICAL AI
# ============================================================

@app.post("/ask")
def ask_question(request: QuestionRequest):

    try:

        history = [
            {
                "role": message.role,
                "content": message.content
            }
            for message in request.history
        ]

        return ask_medical_ai(
            request.question,
            history
        )

    except Exception as e:

        return {
            "error": str(e)
        }


# ============================================================
# STUDY MODE
# ============================================================

@app.post("/study")
def create_study_lesson(request: StudyRequest):

    try:

        return generate_study_lesson(
            request.topic,
            request.difficulty
        )

    except Exception as e:

        return {
            "error": str(e)
        }


# ============================================================
# QUIZ MODE
# ============================================================

@app.post("/quiz")
def create_quiz(request: QuizRequest):

    try:

        return generate_medical_quiz(
            request.topic,
            request.difficulty
        )

    except Exception as e:

        return {
            "error": str(e)
        }