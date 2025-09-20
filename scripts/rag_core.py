# scripts/rag_core.py (Revised for yielding messages with improved Fanar translation handling)

import os
import json
from dotenv import load_dotenv
import requests
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from scripts.conversation_manager import ConversationManager
from langdetect import detect
from typing import List
from langchain.schema import Document


SYSTEM_PROMPT = (
    "You are an AI assistant that ONLY answers using the context provided. "
    "Do NOT use prior knowledge. "
    "If the context does not contain the answer, say you don't have enough information. "
    "Answer clearly using bullet points starting with '- '. "
    "Do not include side notes or introductions. "
    "If the topic is football, always interpret it as soccer (association football), NOT American football."
    "Don't give such long answers that the user has to scroll to read them. "
    "Answer ONLY with concise bullet points from the snippets."
    "Do not explain the language of the snippets."
    "Do not mention translations or the source language."
    "Only return the rules/content directly."

)


conv_manager = ConversationManager(system_prompt=SYSTEM_PROMPT)

load_dotenv()

FANAR_API_KEY = os.getenv("FANAR_API_KEY")
FANAR_API_URL = "https://api.fanar.qa/v1/chat/completions"

if not FANAR_API_KEY:
    raise ValueError("FANAR_API_KEY not found in .env file.")

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
FAISS_DB_DIR = os.path.join(PROJECT_ROOT, "vector2_db")

_embedder = None
_db = None
_conversation = None

_embedder = None
_value_db = None
_cultural_db = None

def make_rtl(text):
    return "\u202B" + text + "\u202C"

def convert_bullets_to_arabic(text):
    return text.replace("- ", "• ")


def translate_text_fanar(text, source_lang, target_lang):
    url = "https://api.fanar.qa/v1/translations"
    headers = {
        "Authorization": f"Bearer {FANAR_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "Fanar-Shaheen-MT-1",
        "text": text,
        "langpair": f"{source_lang}-{target_lang}",
        "preprocessing": "default"
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()
    print("[DEBUG] Translation API response:", data)
    return data.get("text") or data.get("translated_text") or data.get("translation") or ""


def detect_football_type(query: str, lang: str) -> str:
    if "كرة القدم" in query and lang == "ar":
        return "soccer"
    if "football" in query.lower() and lang == "en":
        return "soccer"
    return "soccer"


def generate_fanar_response(messages, model="Fanar"):
    headers = {
        "Authorization": f"Bearer {FANAR_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": 300,
    }

    print(f"[DEBUG] Sending payload to Fanar API:\n{json.dumps(payload, indent=2)}")

    try:
        response = requests.post(FANAR_API_URL, headers=headers, json=payload)
        print(f"[DEBUG] Fanar API response status: {response.status_code}")
        print(f"[DEBUG] Fanar API response body:\n{response.text}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f"[ERROR] Fanar API HTTP error: {http_err}")
        raise
    except Exception as e:
        print(f"[ERROR] General exception during Fanar API call: {e}")
        raise

def _load_embedder():
    global _embedder
    if _embedder is None:
        _embedder = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)

def _load_vector_db():
    global _db
    _load_embedder()
    if _db is None:
        _db = FAISS.load_local(FAISS_DB_DIR, _embedder, allow_dangerous_deserialization=True)

def safe_generate_answer(fanar_response: str) -> str:
    if "not explicitly stated" in fanar_response.lower():
        return f"⚠️ Note: Some parts were not explicitly found in the database. Here is what was retrieved:\n\n{fanar_response}"
    return fanar_response

def expand_query(query: str) -> List[str]:
    """Expand the query with soccer, basketball, tennis, padel, swimming, cardio, yoga, warm-up, cooldown, HIIT, and stretching synonyms."""
    expansions = {
        # Football
        "football rules": [
            "soccer rules",
            "FIFA rules",
            "laws of the game",
            "association football regulations"
        ],
        "football positions": [
            "soccer positions",
            "striker",
            "midfielder",
            "defender",
            "goalkeeper"
        ],
        "football training": [
            "soccer drills",
            "soccer practice",
            "ball control exercises",
            "passing drills",
            "shooting drills"
        ],
        # Basketball
        "basketball rules": [
            "FIBA rules",
            "basketball regulations",
            "official basketball rules"
        ],
        "basketball positions": [
            "point guard",
            "shooting guard",
            "small forward",
            "power forward",
            "center"
        ],
        "basketball training": [
            "basketball drills",
            "shooting practice",
            "dribbling drills",
            "defensive drills"
        ],
        # Tennis
        "tennis rules": [
            "ITF rules",
            "tennis regulations",
            "tennis scoring system"
        ],
        "tennis training": [
            "tennis drills",
            "serve practice",
            "forehand drills",
            "backhand drills"
        ],
        # Padel
        "padel rules": [
            "padel regulations",
            "official padel rules",
            "world padel tour rules"
        ],
        "padel training": [
            "padel drills",
            "padel forehand",
            "padel backhand",
            "padel serve practice"
        ],
        # Swimming
        "swimming styles": [
            "swimming strokes",
            "butterfly stroke",
            "backstroke",
            "breaststroke",
            "freestyle"
        ],
        "swimming training": [
            "swimming drills",
            "swimming endurance",
            "kickboard exercises"
        ],
        # Cardio
        "cardio exercise": [
            "aerobic exercise",
            "endurance training",
            "running",
            "cycling",
            "jump rope"
        ],
        # Yoga
        "yoga": [
            "asanas",
            "yoga poses",
            "yoga practice",
            "yoga breathing",
            "yoga styles"
        ],
        # Warm-up
        "warm up": [
            "pre-exercise warmup",
            "dynamic stretching",
            "mobility exercises"
        ],
        # Cooldown
        "cooldown": [
            "post-exercise cooldown",
            "static stretching",
            "relaxation exercises"
        ],
        # HIIT
        "hiit": [
            "high intensity interval training",
            "interval workouts",
            "tabata training"
        ],
        # Stretching
        "stretching": [
            "flexibility exercises",
            "mobility drills",
            "static stretches",
            "dynamic stretches"
        ],
    }

    if "football" in query.lower():
        query = query.replace("football", "soccer (association football)")

    for key, extra_terms in expansions.items():
        if key in query.lower():
            return [query] + extra_terms

    return [query]

def retrieve_relevant_docs(query: str, vectorstore, k: int = 8) -> List[Document]:
    """Retrieve docs with query expansion and debugging output."""
    expanded_queries = expand_query(query)
    all_docs = []

    for q in expanded_queries:
        docs = vectorstore.similarity_search(q, k=k)
        all_docs.extend(docs)

    seen = set()
    unique_docs = []
    for d in all_docs:
        if d.page_content not in seen:
            seen.add(d.page_content)
            unique_docs.append(d)

    for doc in unique_docs[:5]: 
        print("[DEBUG] Retrieved:", doc.metadata.get("source", ""), doc.page_content[:300])

    return unique_docs

def generate_response(user_query, retrieved_docs, conv_manager):
    if not retrieved_docs:
        return "⚠️ The database does not contain this information."

    context_snippets = []
    for doc in retrieved_docs:
        snippet = doc.page_content.strip()
        if len(snippet) > 400:
            snippet = snippet[:400] + "..."
        context_snippets.append(snippet)

    context = "Here are the ONLY database snippets you can use:\n" + "\n".join(f"- {s}" for s in context_snippets)

    combined_input = f"Question: {user_query}\n\n{context}\n\n" \
                    f"Answer clearly and concisely, prioritizing ONLY the above snippets. " \
                    f"If something is not in them, you may briefly state it is missing, but do not fabricate details."


    conv_manager.add_user_message(combined_input)

    try:
        fanar_response = generate_fanar_response(conv_manager.get_messages()[-6:])
        generated_text = fanar_response["choices"][0]["message"]["content"].strip()

        if any(keyword in generated_text.lower() for keyword in [
            "not explicitly stated", "we can infer", "although not mentioned", "let me give a more complete version"
        ]):
            return f"⚠️ Some details may not be explicitly in the database. Here’s what was retrieved:\n\n{generated_text}"


        conv_manager.add_assistant_message(generated_text)
        return generated_text

    except Exception as e:
        return f"⚠️ An error occurred while generating a response: {str(e)}"



def detect_language(text):
    try:
        lang = detect(text)
        return lang
    except:
        return "unknown"




def run_rag_pipeline(query, conv_manager):
    yield json.dumps({"type": "status", "message": "Received user query..."})

    try:
        desired_lang = detect_answer_language_override(query)
        print(f"[DEBUG] Language override detected: {desired_lang}")

        detected_lang = detect_language(query)
        print(f"[DEBUG] Detected language: {detected_lang}")

        if desired_lang:
            answer_lang = desired_lang
        elif detected_lang in ["ar", "fa", "fas", "per"]:
            answer_lang = detected_lang
        else:
            answer_lang = "en"

        if detected_lang == "ar":
            try:
                query_en = translate_text_fanar(query, "ar", "en")
            except Exception:
                warning_msg = "⚠️ Failed to translate Arabic query to English."
                print("[WARN]", warning_msg)
                yield json.dumps({"type": "status", "message": warning_msg})
                query_en = query
        elif detected_lang == "fa":
            try:
                query_en = translate_text_fanar(query, "fa", "en")
            except Exception:
                warning_msg = "⚠️ Failed to translate Persian query to English."
                print("[WARN]", warning_msg)
                yield json.dumps({"type": "status", "message": warning_msg})
                query_en = query
        else:
            query_en = query

        yield json.dumps({"type": "status", "message": "Searching vector DB..."})

        _load_vector_db()
        docs = retrieve_relevant_docs(query_en, _db)

        yield json.dumps({"type": "status", "message": "Generating response..."})
        reply_en = generate_response(query_en, docs, conv_manager)

        if answer_lang == "ar":
            try:
                yield json.dumps({"type": "status", "message": "Translating response back to Arabic..."})
                reply_final = translate_text_fanar(reply_en, "en", "ar")
                if reply_final.strip():
                    reply_final = convert_bullets_to_arabic(reply_final)
                    reply_final = make_rtl(reply_final)
                else:
                    reply_final = make_rtl(reply_en)
            except Exception:
                reply_final = make_rtl(reply_en)
        elif answer_lang == "fa":
            try:
                yield json.dumps({"type": "status", "message": "Translating response back to Persian..."})
                reply_final = translate_text_fanar(reply_en, "en", "fa")
                if reply_final.strip():
                    reply_final = make_rtl(reply_final)
                else:
                    reply_final = make_rtl(reply_en)
            except Exception:
                reply_final = make_rtl(reply_en)
        else:
            reply_final = reply_en

        yield json.dumps({"type": "bot_response", "message": reply_final})

    except Exception as e:
        yield json.dumps({"type": "error", "message": f"An error occurred: {str(e)}"})

def detect_answer_language_override(text):
    text = text.lower().strip()
    text = text.replace("إ", "ا").replace("أ", "ا")  
    if any(kw in text for kw in ["answer in arabic", "in arabic", "arabic", "ans in arabic", "باللغة العربيه", "اجب بالعربيه"]):
        return "ar"
        
    if any(kw in text for kw in ["answer in english", "ans in english", "in english", "english", "باللغة الانجليزيه", "اجب بالانجليزيه"]):
        return "en"
    
    if any(kw in text for kw in ["answer in persian", "answer in farsi", "in persian", "in farsi", "بالفارسية", "اجب بالفارسية"]):
        return "fa"

    return None


# Usage Example:
# from rag_core import run_rag_pipeline, ConversationManager, SYSTEM_PROMPT
# conv_manager = ConversationManager(SYSTEM_PROMPT)
# for chunk in run_rag_pipeline("What are the basic rules of football?", conv_manager):
#     print(chunk)