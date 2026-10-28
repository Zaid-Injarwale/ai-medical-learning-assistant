import os
import re
import unicodedata
import requests
from typing import Literal

from dotenv import load_dotenv
from google import genai
from google.genai import errors
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
# IMAGE INFORMATION
# ============================================================

class ImageInfo(BaseModel):

    required: bool

    search_query: str = ""

    image_url: str = ""

    title: str = ""

    source_url: str = ""


# ============================================================
# VISUAL INFORMATION
# ============================================================

class Visual(BaseModel):

    required: bool

    type: Literal[
        "anatomy_diagram",
        "physiology_diagram",
        "pathology_diagram",
        "flowchart",
        "comparison",
        "none"
    ]

    topic: str


# ============================================================
# GEMINI RESPONSE
# ============================================================

class GeminiMedicalResponse(BaseModel):

    answer: str = Field(
        description=(
            "Clear, slightly detailed medical explanation "
            "appropriate for the student's question."
        )
    )

    difficulty: Literal[
        "basic",
        "intermediate",
        "advanced"
    ]

    key_points: list[str]

    memory_aid: str

    visual: Visual

    image_search_query: str = Field(
        default="",
        description=(
            "Specific educational medical image search query. "
            "Example: heart anatomy diagram"
        )
    )


# ============================================================
# FINAL RESPONSE SENT TO FRONTEND
# ============================================================

class MedicalLearningResponse(BaseModel):

    answer: str

    difficulty: Literal[
        "basic",
        "intermediate",
        "advanced"
    ]

    key_points: list[str]

    memory_aid: str

    visual: Visual

    image: ImageInfo


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are an expert medical education AI.

Your job is to teach medical students clearly, accurately,
and in an easy-to-understand way.

IMPORTANT RULES:

1. Understand the student's question before answering.

2. Automatically determine the appropriate difficulty:
   - basic
   - intermediate
   - advanced

3. Basic questions should receive a clear explanation that is
   slightly longer than a one-line definition.

   Usually provide around 2-4 short paragraphs when appropriate.

4. Intermediate questions should receive a moderately detailed
   explanation covering the important concepts and relationships.

5. Advanced questions should receive deeper and technically accurate
   explanations.

6. Do not unnecessarily make simple questions complicated.

7. Give medically accurate educational information.

8. Include useful points that a medical student should remember.

   Provide approximately:

   - 5-7 key points for basic questions
   - 6-9 key points for intermediate questions
   - 8-12 key points for advanced questions

   Key points must contain useful and specific information.

   Do NOT simply repeat the answer sentence by sentence.

   Where appropriate, key points can include:
   - important structures
   - functions
   - mechanisms
   - classifications
   - important terminology
   - clinical relevance
   - relationships between concepts
   - important exam facts

9. Give a useful memory aid whenever possible.

   Prefer:
   - mnemonics
   - simple associations
   - memorable comparisons
   - short patterns
   - easy recall tricks

   The memory aid should actually help a medical student
   remember the topic.

10. Use the previous conversation when answering follow-up questions.

    If the student uses words such as:
    - it
    - this
    - that
    - these
    - those
    - which one
    - why
    - how
    - the above
    - the previous one

    use the conversation history to understand what they mean.

11. Do not ask the student to repeat information that is already
    available in the conversation history.

12. Answer the current question directly.

    Use previous conversation only when it provides useful context.

13. Decide whether a medical educational visual is useful.

14. For anatomy, organs, structures, physiological processes,
    pathology, mechanisms and comparisons, an educational image
    is usually useful.

15. If an image is useful:

    visual.required = true

16. Choose the appropriate visual type:

    - anatomy_diagram
    - physiology_diagram
    - pathology_diagram
    - flowchart
    - comparison

17. If an image is useful, provide a concise and specific
    image_search_query.

Examples:

Question:
"What is the heart?"

image_search_query:
"heart anatomy diagram"

Question:
"What is the pancreas?"

image_search_query:
"pancreas anatomy diagram"

Question:
"Explain nephron"

image_search_query:
"nephron anatomy diagram"

Question:
"What is glycolysis?"

image_search_query:
"glycolysis pathway diagram"

Question:
"Explain pulmonary circulation"

image_search_query:
"pulmonary circulation diagram"

18. Do NOT use extremely long image queries.

19. Do NOT use vague queries such as:
    "heart"
    "pancreas"
    "liver"

20. Do NOT diagnose the student.

21. Do NOT prescribe treatment.

22. Focus on medical education.

23. For very simple questions, do not create an unnecessarily
    long essay. Keep the explanation useful and focused.

24. When the question is a follow-up question, maintain continuity
    with the previous conversation.

25. Avoid repeating large portions of previous answers unless
    repetition is necessary for understanding.
"""


# ============================================================
# FALLBACK IMAGE QUERY
# ============================================================

def create_fallback_image_query(question: str) -> str:

    question = question.strip()

    if not question:
        return ""

    return f"{question} anatomy diagram"



# ============================================================
# TRUSTED ENGLISH DIAGRAMS
# ============================================================
# Wikimedia search can return an image whose FILE TITLE is English
# while the actual labels are in another language. For common core
# anatomy topics, use known English-labelled Commons files first.
#
# These are exact Wikimedia Commons file titles, so they bypass the
# unreliable "search result title looks English" problem.
PREFERRED_ENGLISH_WIKIMEDIA_FILES = {
    "kidney": [
        "File:Blausen 0592 KidneyAnatomy 01.png",
        "File:Kidney Cross Section.png",
    ],
}

# ============================================================
# SEARCH WIKIMEDIA COMMONS
#
# STEP 1:
# Search the File namespace using list=search.
# ============================================================

def search_wikimedia_files(query: str) -> list[str]:

    if not query:
        return []

    url = "https://commons.wikimedia.org/w/api.php"

    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srnamespace": 6,
        "srlimit": 20,
        "srwhat": "text",
        "format": "json",
    }

    headers = {
        "User-Agent": (
            "MedicalLearningAssistant/1.0 "
            "(educational local application)"
        )
    }

    try:

        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        results = (
            data
            .get("query", {})
            .get("search", [])
        )

        titles = []

        for result in results:

            title = result.get(
                "title",
                ""
            )

            if title:
                titles.append(title)

        return titles

    except Exception as e:

        print(
            "Wikimedia search error:",
            e
        )

        return []


# ============================================================
# GET IMAGE INFORMATION
# ============================================================

def get_wikimedia_image_info(
    titles: list[str]
) -> list[dict]:

    if not titles:
        return []

    url = "https://commons.wikimedia.org/w/api.php"

    params = {
        "action": "query",
        "titles": "|".join(titles),
        "prop": "imageinfo",
        "iiprop": "url|extmetadata",
        "iiurlwidth": 1000,
        "format": "json",
    }

    headers = {
        "User-Agent": (
            "MedicalLearningAssistant/1.0 "
            "(educational local application)"
        )
    }

    try:

        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        pages = (
            data
            .get("query", {})
            .get("pages", {})
        )

        results = []

        for page in pages.values():

            title = page.get(
                "title",
                ""
            )

            imageinfo = page.get(
                "imageinfo",
                []
            )

            if not imageinfo:
                continue

            info = imageinfo[0]

            image_url = (
                info.get("thumburl")
                or info.get("url")
                or ""
            )

            source_url = info.get(
                "descriptionurl",
                ""
            )

            if not image_url:
                continue

            results.append({
                "title": title,
                "image_url": image_url,
                "source_url": source_url
            })

        return results

    except Exception as e:

        print(
            "Wikimedia imageinfo error:",
            e
        )

        return []


# ============================================================
# MEDICAL IMAGE TOPIC HELPERS
# ============================================================

IMAGE_TOPIC_ALIASES = {
    "cardiac cycle": [
        "cardiac cycle diagram",
        "cardiac cycle phases diagram",
        "heart cardiac cycle diagram"
    ],
    "heart": [
        "heart anatomy labeled diagram",
        "human heart anatomy diagram"
    ],
    "nephron": [
        "nephron labeled diagram",
        "nephron anatomy diagram"
    ],
    "glomerular filtration": [
        "glomerular filtration diagram",
        "glomerulus bowman capsule diagram"
    ],
    "pulmonary circulation": [
        "pulmonary circulation diagram",
        "pulmonary circulation pathway diagram"
    ],
    "systemic circulation": [
        "systemic circulation diagram",
        "systemic circulation pathway diagram"
    ],
    "double circulation": [
        "double circulation diagram",
        "human double circulation diagram"
    ],
    "glycolysis": [
        "glycolysis pathway diagram",
        "glycolysis steps diagram"
    ],
    "krebs cycle": [
        "Krebs cycle diagram",
        "citric acid cycle diagram"
    ],
    "citric acid cycle": [
        "Krebs cycle diagram",
        "citric acid cycle diagram"
    ],
    "electron transport chain": [
        "electron transport chain diagram",
        "oxidative phosphorylation diagram"
    ],
    "oxidative phosphorylation": [
        "oxidative phosphorylation diagram",
        "electron transport chain diagram"
    ],
    "mitosis": [
        "mitosis stages labeled diagram",
        "mitosis cell division diagram"
    ],
    "meiosis": [
        "meiosis stages labeled diagram",
        "meiosis cell division diagram"
    ],
    "action potential": [
        "action potential graph diagram",
        "action potential physiology diagram"
    ],
    "synapse": [
        "chemical synapse labeled diagram",
        "synaptic transmission diagram"
    ],
    "neuron": [
        "neuron labeled diagram",
        "neuron anatomy diagram"
    ],
    "blood clotting": [
        "blood coagulation cascade diagram",
        "blood clotting pathway diagram"
    ],
    "coagulation": [
        "blood coagulation cascade diagram",
        "coagulation pathway diagram"
    ],
    "hemostasis": [
        "hemostasis process diagram",
        "blood clotting pathway diagram"
    ],
    "respiratory system": [
        "human respiratory system labeled diagram",
        "respiratory system anatomy diagram"
    ],
    "digestive system": [
        "human digestive system labeled diagram",
        "digestive system anatomy diagram"
    ],
    "liver": [
        "liver anatomy labeled diagram",
        "human liver anatomy diagram"
    ],
    "pancreas": [
        "pancreas anatomy labeled diagram",
        "human pancreas anatomy diagram"
    ],
    "kidney": [
        "kidney anatomy labeled diagram",
        "human kidney anatomy diagram",
        "renal anatomy labeled diagram"
    ],
    "brain": [
        "human brain anatomy labeled diagram",
        "brain anatomy diagram"
    ],
    "spinal cord": [
        "spinal cord anatomy labeled diagram",
        "spinal cord cross section diagram"
    ],
    "skeletal system": [
        "human skeletal system labeled diagram",
        "skeletal system anatomy diagram"
    ],
    "muscular system": [
        "human muscular system labeled diagram",
        "muscular system anatomy diagram"
    ],
    "endocrine system": [
        "human endocrine system labeled diagram",
        "endocrine glands anatomy diagram"
    ],
    "immune system": [
        "immune system diagram",
        "immune response diagram"
    ],
    "menstrual cycle": [
        "menstrual cycle phases diagram",
        "menstrual cycle hormone graph diagram"
    ],
    "renin angiotensin": [
        "renin angiotensin aldosterone system diagram",
        "RAAS pathway diagram"
    ],
    "raas": [
        "renin angiotensin aldosterone system diagram",
        "RAAS pathway diagram"
    ],
}

# A candidate must contain at least one of these topic-specific
# words in its Wikimedia title. This prevents a general abdomen
# or whole-body plate from being returned for a kidney question.
IMAGE_TOPIC_REQUIRED_WORDS = {
    "kidney": {"kidney", "kidneys", "renal", "nephron", "urinary"},
    "nephron": {"nephron", "kidney", "renal"},
    "glomerular filtration": {"glomerular", "glomerulus", "nephron", "bowman", "kidney"},
    "heart": {"heart", "cardiac"},
    "cardiac cycle": {"cardiac", "heart"},
    "liver": {"liver", "hepatic"},
    "pancreas": {"pancreas", "pancreatic"},
    "brain": {"brain", "cerebral", "cerebrum", "cerebell"},
    "spinal cord": {"spinal", "cord"},
    "lung": {"lung", "lungs", "pulmonary"},
    "respiratory system": {"respiratory", "lung", "lungs", "airway"},
    "digestive system": {"digestive", "gastrointestinal", "intestine", "stomach"},
}


def normalize_image_text(value: str) -> str:
    value = value.lower()
    # Remove accents so terms such as "riñón" remain searchable as "rinon".
    value = unicodedata.normalize("NFKD", value)
    value = "".join(
        char for char in value
        if not unicodedata.combining(char)
    )
    value = value.replace("-", " ")
    value = value.replace("_", " ")
    value = value.replace("/", " ")
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


# Prefer English-labelled educational diagrams. Wikimedia contains many
# otherwise relevant anatomy plates with labels in Spanish, French, German,
# Portuguese, Italian, etc. Reject obvious non-English title markers so the
# student does not receive a diagram they cannot easily read.
NON_ENGLISH_IMAGE_MARKERS = {
    # Spanish
    "anatomia del", "rinon", "riñon", "corazon", "pulmon",
    "medula renal", "corteza renal", "piramides renales",
    "capsula renal", "caliz mayor", "caliz menor",
    # French
    "anatomie du", "anatomie de", "rein humain", "coeur humain",
    "cortex renal", "medulla renal",
    # German
    "niere anatomie", "herz anatomie", "gehirn anatomie",
    # Portuguese
    "anatomia do", "anatomia da", "rim humano", "coracao humano",
    # Italian
    "anatomia del rene", "rene umano", "cuore umano",
}


def looks_non_english_image(title: str) -> bool:
    normalized = normalize_image_text(title)
    raw = title.lower()

    for marker in NON_ENGLISH_IMAGE_MARKERS:
        marker_normalized = normalize_image_text(marker)
        if marker_normalized in normalized:
            return True

    # Common unmistakable Spanish words in image titles.
    spanish_words = {
        "anatomia", "rinon", "corazon", "pulmones", "cerebro",
        "higado", "pancreas", "arteria", "vena", "ureter",
        "medula", "corteza", "capsula", "piramides", "caliz",
        "renal", "renales",
    }
    words = set(normalized.split())

    # Require multiple language markers to avoid rejecting a legitimate
    # English title containing a shared medical word such as "renal".
    if len(words.intersection(spanish_words)) >= 2:
        return True

    return False


def get_focused_image_queries(
    question: str,
    gemini_query: str
) -> list[str]:

    question_text = normalize_image_text(question)
    gemini_text = normalize_image_text(gemini_query)

    queries = []

    # Prefer a known medical topic over a vague Gemini query.
    for topic, topic_queries in IMAGE_TOPIC_ALIASES.items():

        if topic in question_text or topic in gemini_text:

            queries.extend(
                query + " English labeled diagram"
                for query in topic_queries
            )

            # One focused topic is enough. Do not mix
            # unrelated anatomy topics into the search.
            break

    if not queries and gemini_text:
        queries.append(gemini_query.strip() + " English medical diagram")

    if not queries:
        queries.append(
            question.strip() + " English medical diagram"
        )

    # Remove duplicates while preserving order.
    return list(
        dict.fromkeys(
            query for query in queries
            if query.strip()
        )
    )[:3]


def get_image_topic(question: str, gemini_query: str) -> str:
    question_text = normalize_image_text(question)
    gemini_text = normalize_image_text(gemini_query)

    for topic in IMAGE_TOPIC_ALIASES:
        if topic in question_text or topic in gemini_text:
            return topic

    return ""


def score_medical_image(
    title: str,
    query: str,
    topic: str = ""
) -> int:

    title_text = normalize_image_text(title)
    query_text = normalize_image_text(query)

    score = 0

    # Do not select diagrams whose title strongly indicates a non-English
    # label set. We prefer a readable English educational image.
    if looks_non_english_image(title):
        return -1000

    positive_words = {
        "diagram": 8,
        "anatomy": 8,
        "anatomical": 8,
        "labeled": 7,
        "labelled": 7,
        "medical": 5,
        "physiology": 6,
        "pathology": 6,
        "organ": 4,
        "pathway": 5,
        "cycle": 5,
        "cascade": 5,
        "stages": 4,
        "mechanism": 4,
        "illustration": 3,
    }

    for word, points in positive_words.items():
        if word in title_text:
            score += points

    query_words = [
        word for word in query_text.split()
        if len(word) >= 4
    ]

    for word in query_words:
        if word in title_text:
            score += 5

    if query_text and query_text in title_text:
        score += 25

    # English educational wording is preferred.
    for word in ("english", "labeled", "labelled", "anatomy", "anatomical"):
        if word in title_text:
            score += 3

    # Critical topic check.
    # If we know the question is about a kidney, a title such as
    # "anatomy of abdomen" is NOT acceptable even if it is medical.
    required_words = IMAGE_TOPIC_REQUIRED_WORDS.get(topic, set())

    if required_words:
        topic_match = any(
            word in title_text
            for word in required_words
        )

        if not topic_match:
            return -1000

        score += 35

    negative_words = {
        "book": -35,
        "cover": -35,
        "treatise": -35,
        "journal": -30,
        "magazine": -30,
        "portrait": -30,
        "person": -20,
        "building": -25,
        "museum": -25,
        "painting": -25,
        "statue": -25,
        "logo": -25,
        "flag": -25,
        "stamp": -25,
        "novel": -35,
        "pdf": -35,
        "poster": -20,
        "photograph": -10,
        "photo": -10,
    }

    for word, points in negative_words.items():
        if word in title_text:
            score += points

    return score


# ============================================================
# MAIN IMAGE SEARCH FUNCTION
# ============================================================

def search_medical_image(
    query: str,
    question: str = "",
    visual_type: str = "none"
) -> ImageInfo:

    if not query and not question:

        return ImageInfo(
            required=False,
            search_query="",
            image_url="",
            title="",
            source_url=""
        )

    print()
    print("========================================")
    print("MEDICAL IMAGE SEARCH")
    print("========================================")

    focused_queries = get_focused_image_queries(
        question,
        query
    )

    image_topic = get_image_topic(
        question,
        query
    )

    print(
        "Focused image queries:",
        focused_queries
    )

    print(
        "Visual type:",
        visual_type
    )

    print(
        "Detected image topic:",
        image_topic
    )

    # --------------------------------------------------------
    # STEP 1
    # For core topics, try trusted English-labelled files first.
    # This prevents a Spanish/French/etc. diagram from winning
    # simply because Wikimedia ranked it highly.
    # --------------------------------------------------------

    preferred_titles = PREFERRED_ENGLISH_WIKIMEDIA_FILES.get(
        image_topic,
        []
    )

    all_titles = []

    if preferred_titles:
        print(
            "Trying trusted English diagrams:",
            preferred_titles
        )

        preferred_results = get_wikimedia_image_info(
            preferred_titles
        )

        if preferred_results:
            print(
                "Trusted English diagrams found:",
                len(preferred_results)
            )

            # For a topic with trusted diagrams, use these candidates
            # instead of letting an unrelated Wikimedia result win.
            image_results = preferred_results
        else:
            image_results = []
    else:
        image_results = []

    # --------------------------------------------------------
    # STEP 2
    # If no trusted file was available, use normal Wikimedia search.
    # --------------------------------------------------------

    if not image_results:
        for search_query in focused_queries:

            print(
                "Searching Wikimedia:",
                search_query
            )

            titles = search_wikimedia_files(
                search_query
            )

            all_titles.extend(titles)


    # Remove duplicate Wikimedia titles.
    all_titles = list(
        dict.fromkeys(
            title for title in all_titles
            if title
        )
    )

    print(
        "Unique files found:",
        len(all_titles)
    )

    # --------------------------------------------------------
    # If normal focused searches failed, use the original query
    # and a small number of safe fallbacks.
    # --------------------------------------------------------

    if not image_results and not all_titles:

        fallback_queries = [
            query.replace(
                "labeled",
                ""
            ).replace(
                "labelled",
                ""
            ).strip(),

            query.replace(
                "anatomy",
                ""
            ).strip(),

            "medical " + query
        ]

        fallback_queries = list(
            dict.fromkeys(
                q for q in fallback_queries
                if q
            )
        )

        for fallback_query in fallback_queries:

            print(
                "Trying fallback:",
                fallback_query
            )

            titles = search_wikimedia_files(
                fallback_query
            )

            all_titles.extend(titles)

            if all_titles:
                break

    if not image_results and not all_titles:

        print(
            "NO WIKIMEDIA FILES FOUND"
        )

        print(
            "========================================"
        )

        return ImageInfo(
            required=False,
            search_query=query,
            image_url="",
            title="",
            source_url=""
        )

    # --------------------------------------------------------
    # STEP 2
    # Get actual image information.
    # --------------------------------------------------------

    if not image_results:
        image_results = get_wikimedia_image_info(
            all_titles
        )

    if not image_results:

        print(
            "Wikimedia returned files but no image URLs."
        )

        print(
            "========================================"
        )

        return ImageInfo(
            required=False,
            search_query=query,
            image_url="",
            title="",
            source_url=""
        )

    # --------------------------------------------------------
    # STEP 3
    # Score every candidate against every focused query.
    # --------------------------------------------------------

    scored_results = []

    for result in image_results:

        best_candidate_score = -999

        for focused_query in focused_queries:

            score = score_medical_image(
                result["title"],
                focused_query,
                image_topic
            )

            if score > best_candidate_score:
                best_candidate_score = score

        scored_results.append(
            (
                best_candidate_score,
                result
            )
        )

    scored_results.sort(
        key=lambda item: item[0],
        reverse=True
    )

    print()
    print("TOP IMAGE CANDIDATES:")

    for score, result in scored_results[:5]:

        print(
            score,
            "->",
            result["title"]
        )

    best_score, best_result = (
        scored_results[0]
    )

    # Do not show a random Wikimedia image when the
    # title has almost no relationship to the question.
    if best_score < 8:

        print(
            "Best image score too low:",
            best_score
        )

        print(
            "No sufficiently relevant medical image found."
        )

        print(
            "========================================"
        )

        return ImageInfo(
            required=False,
            search_query=query,
            image_url="",
            title="",
            source_url=""
        )

    print()
    print("BEST IMAGE:")
    print(
        "Title:",
        best_result["title"]
    )
    print(
        "Score:",
        best_score
    )
    print(
        "Image URL:",
        best_result["image_url"]
    )
    print(
        "Source:",
        best_result["source_url"]
    )
    print(
        "========================================"
    )

    return ImageInfo(
        required=True,
        search_query=focused_queries[0],
        image_url=best_result["image_url"],
        title=best_result["title"],
        source_url=best_result["source_url"]
    )


# ============================================================
# ASK GEMINI
# ============================================================

def ask_medical_ai(
    question: str,
    history: list[dict] | None = None
) -> MedicalLearningResponse:

    question = question.strip()

    if history is None:
        history = []

    if not question:

        raise RuntimeError(
            "Please enter a medical question."
        )

    # ========================================================
    # CONVERSATION MEMORY
    # ========================================================

    conversation_text = ""

    if history:

        conversation_text = (
            "\nPrevious conversation:\n\n"
        )

        # Keep the most recent 10 messages.
        # This prevents the prompt from becoming unnecessarily large.

        for message in history[-10:]:

            role = message.get(
                "role",
                ""
            )

            content = message.get(
                "content",
                ""
            )

            if not content:
                continue

            if role == "user":

                conversation_text += (
                    f"Student: {content}\n"
                )

            elif role == "assistant":

                conversation_text += (
                    f"AI Tutor: {content}\n"
                )

            conversation_text += "\n"

    # ========================================================
    # FINAL PROMPT
    # ========================================================

    prompt = f"""
{SYSTEM_PROMPT}

{conversation_text}

Current student question:

{question}
"""

    try:

        # ====================================================
        # GEMINI
        # ====================================================

        response = client.models.generate_content(

            model="gemini-3.5-flash-lite",

            contents=prompt,

            config={

                "response_mime_type": "application/json",

                "response_schema":
                    GeminiMedicalResponse,

                "thinking_config": {
                    "thinking_level": "low"
                },
            },
        )

        result = response.parsed

        if result is None:

            raise RuntimeError(
                "Gemini returned an empty response."
            )

        # ====================================================
        # DEBUG
        # ====================================================

        print()
        print("========================================")
        print("GEMINI RESULT")
        print("========================================")

        print(
            "Difficulty:",
            result.difficulty
        )

        print(
            "Visual required:",
            result.visual.required
        )

        print(
            "Visual type:",
            result.visual.type
        )

        print(
            "Number of key points:",
            len(result.key_points)
        )

        print(
            "Gemini image query:",
            result.image_search_query
        )

        print(
            "========================================"
        )

        # ====================================================
        # IMAGE QUERY
        # ====================================================

        image_query = (
            result.image_search_query.strip()
        )

        if not image_query:

            image_query = (
                create_fallback_image_query(
                    question
                )
            )

            print(
                "Using fallback image query:",
                image_query
            )

        # ====================================================
        # SEARCH IMAGE
        #
        # We do not depend on Gemini's
        # image.required field.
        #
        # Python creates the final ImageInfo.
        # ====================================================

        image = search_medical_image(
            image_query,
            question=question,
            visual_type=result.visual.type
        )

        # ====================================================
        # FINAL VISUAL INFORMATION
        # ====================================================

        visual = result.visual

        if image.required:

            if visual.type == "none":

                visual = Visual(
                    required=True,
                    type="anatomy_diagram",
                    topic=question
                )

            else:

                visual.required = True

        # ====================================================
        # FINAL RESPONSE
        # ====================================================

        return MedicalLearningResponse(

            answer=result.answer,

            difficulty=result.difficulty,

            key_points=result.key_points,

            memory_aid=result.memory_aid,

            visual=visual,

            image=image
        )

    # ========================================================
    # GEMINI SERVER ERROR
    # ========================================================

    except errors.ServerError as e:

        if getattr(
            e,
            "status_code",
            None
        ) == 503:

            raise RuntimeError(
                "Gemini is temporarily overloaded. "
                "Please try again in a few seconds."
            )

        raise

    # ========================================================
    # OTHER ERRORS
    # ========================================================

    except Exception as e:

        raise RuntimeError(
            f"Gemini request failed: {str(e)}"
        )