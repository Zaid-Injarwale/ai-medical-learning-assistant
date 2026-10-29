# 🩺 AI Medical Learning Assistant

An AI-powered medical learning platform designed to help students understand medical topics through interactive explanations, structured study lessons, quizzes, and educational medical images.

🔗 **Live Demo:** https://ai-medical-learning-assistant.onrender.com

---

## ✨ Features

### 💬 Medical Chat
Ask questions about medical subjects such as:

- Anatomy
- Physiology
- Pathology
- Pharmacology
- Biochemistry
- Other medical topics

The assistant provides structured explanations with difficulty levels, key points, memory aids, and relevant educational images when available.

### 📖 Study Mode
Study a medical topic step-by-step with AI.

Choose a difficulty level:

- Basic
- Intermediate
- Advanced

Study lessons can include:

- Introduction
- Key concepts
- Detailed explanation
- Clinical relevance
- Exam points
- Memory aids

### 📝 Quiz Mode
Test your medical knowledge using AI-generated multiple-choice quizzes.

Features include:

- 5 questions per quiz
- 4 options per question
- Basic / Intermediate / Advanced difficulty
- Instant answer feedback
- Explanations for answers
- Final score
- Quiz review

### 🖼️ Medical Image Support
The application can retrieve relevant educational medical diagrams from Wikimedia Commons to support visual learning.

### 💾 Recent Chats
The frontend can maintain recent conversations locally for easier access during study sessions.

### 📱 Responsive Design
The interface is designed for both:

- 💻 Desktop
- 📱 Mobile

Mobile users get simplified navigation for Chat, Study, and Quiz modes.

---

## 🛠️ Tech Stack

### Frontend
- HTML5
- CSS3
- JavaScript

### Backend
- Python
- FastAPI
- Uvicorn
- Pydantic

### AI
- Google Gemini API

### External Resources
- Wikimedia Commons API

### Deployment
- GitHub
- Render

---

## 🏗️ Project Structure

```text
ai-medical-learning-assistant/
│
└── backend/
    │
    ├── main.py
    ├── ai.py
    ├── quiz.py
    ├── study.py
    ├── test.py
    ├── requirements.txt
    │
    └── frontend/
        ├── index.html
        └── backup_index.html
```

### File Overview

| File | Purpose |
|---|---|
| `main.py` | FastAPI application and API routes |
| `ai.py` | Medical AI response generation and image search |
| `quiz.py` | AI-generated medical quiz functionality |
| `study.py` | AI-generated study lessons |
| `test.py` | Project testing |
| `index.html` | Main frontend interface |
| `requirements.txt` | Python dependencies |

---

## 🔌 API Endpoints

### Home

```http
GET /
```

Serves the frontend application.

### Medical Chat

```http
POST /ask
```

Accepts a medical question and conversation history.

### Study Mode

```http
POST /study
```

Generates a structured medical study lesson.

Example request:

```json
{
  "topic": "Nephron",
  "difficulty": "basic"
}
```

### Quiz Mode

```http
POST /quiz
```

Generates a medical quiz.

Example request:

```json
{
  "topic": "Digestive System",
  "difficulty": "intermediate"
}
```

---

## 🚀 Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/Zaid-Injarwale/ai-medical-learning-assistant.git
```

### 2. Enter the backend directory

```bash
cd ai-medical-learning-assistant/backend
```

### 3. Create a virtual environment

```bash
python -m venv venv
```

### 4. Activate the environment

#### Windows PowerShell

```powershell
.\venv\Scripts\Activate.ps1
```

### 5. Install dependencies

```bash
pip install -r requirements.txt
```

### 6. Configure the Gemini API key

Create a `.env` file inside the `backend` directory:

```env
GEMINI_API_KEY=your_api_key_here
```

Never commit your `.env` file to GitHub.

### 7. Start the FastAPI server

```bash
python -m uvicorn main:app --reload
```

The application will be available at:

```text
http://127.0.0.1:8000
```

---

## ☁️ Deployment

The application is deployed using **Render**.

Deployment configuration:

```text
Root Directory:
backend/

Build Command:
pip install -r requirements.txt

Start Command:
uvicorn main:app --host 0.0.0.0 --port $PORT
```

The Gemini API key is stored securely as an environment variable on Render.

---

## 🔐 Environment Variables

The project requires:

```env
GEMINI_API_KEY=your_api_key_here
```

The API key should never be exposed in source code or committed to GitHub.

---

## 🧠 How It Works

```text
User
  │
  ▼
Web Interface
  │
  ▼
FastAPI Backend
  │
  ├───────────────► Medical Chat
  │
  ├───────────────► Study Mode
  │
  └───────────────► Quiz Mode
          │
          ▼
      Gemini API
          │
          ▼
  Structured Medical Response
          │
          ├── Explanation
          ├── Key Points
          ├── Memory Aid
          ├── Study Lesson
          └── Quiz
```

For visual learning, the application can also retrieve relevant educational images through Wikimedia Commons.

---

## 🎯 Project Goal

The goal of this project is to create a simple and interactive learning assistant that helps medical students study concepts more effectively using AI-powered explanations, structured lessons, quizzes, and visual learning resources.

---

## 📚 Educational Purpose

This application is intended for **educational and study purposes**.

It is not a replacement for qualified healthcare professionals, medical textbooks, clinical guidelines, or professional medical advice.

Users should independently verify important medical information using trusted medical references.

---

## 👨‍💻 Author

**Zaid-Injarwale**

GitHub:  
https://github.com/Zaid-Injarwale

---

## ⭐ Future Improvements

Possible future enhancements include:

- User authentication
- Persistent cloud chat history
- Progress tracking
- More interactive quizzes
- Flashcards
- Spaced-repetition learning
- Medical topic bookmarks
- PDF / notes upload
- Personalized study plans
- More visual learning tools
- Improved clinical case learning

---

## ⭐ If You Find This Project Useful

Consider giving the repository a ⭐ on GitHub!
