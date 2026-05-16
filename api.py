"""
FastAPI backend for the Srečko Kosovel AI Chat.

Endpoints:
    POST /api/chat   — send a message, get Srečko's response
    GET  /api/health  — liveness check
"""

import os
import random
import re
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

root_path = str(Path(__file__).parent)
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from langchain_rag.agent import create_agent
from scripts.utils.db import get_connection

agent = None

GAME_CATEGORY_SLUGS = ("lirika", "avantgardisticna_poezija", "integrali_26")
GAME_BLANK_COUNT = 5
WORD_RE = re.compile(r"[A-Za-zÀ-ž]+(?:[-'][A-Za-zÀ-ž]+)?", re.UNICODE)
TOKEN_RE = re.compile(r"[A-Za-zÀ-ž]+(?:[-'][A-Za-zÀ-ž]+)?|\s+|[^\w\s]+", re.UNICODE)
COMMON_WORDS = {
    "sem", "si", "je", "smo", "ste", "so", "in", "ali", "pa", "da", "ko",
    "kot", "ker", "kaj", "kdo", "kjer", "kam", "kako", "ne", "ni", "na",
    "v", "z", "s", "za", "od", "do", "po", "ob", "pri", "nad", "pod",
    "me", "mi", "te", "ti", "ga", "jo", "jih", "nas", "vas", "se", "še",
    "že", "le", "bi", "bo", "bom", "bila", "bil", "bilo", "biti", "moj",
    "moja", "moje", "tvoj", "ta", "to", "tu", "tam",
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    global agent
    load_dotenv()

    provider = os.getenv("LLM_PROVIDER", "ollama")
    llm_config = {
        "provider": provider,
        "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        "model": os.getenv("OLLAMA_CHAT_MODEL", "llama3.2:3b"),
        "timeout": int(os.getenv("OLLAMA_CHAT_TIMEOUT", "600")),
    }

    if provider == "openrouter":
        llm_config["model"] = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash-lite")
        llm_config["api_key"] = os.getenv("OPENROUTER_API_KEY")
        llm_config["max_tokens"] = int(os.getenv("OPENROUTER_MAX_TOKENS", "2000"))
    elif provider == "anthropic":
        llm_config["model"] = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")
        llm_config["api_key"] = os.getenv("ANTHROPIC_API_KEY")
    elif provider == "github-copilot":
        llm_config["model"] = os.getenv("GITHUB_COPILOT_MODEL", "Claude Sonnet 4.5")
        llm_config["api_key"] = os.getenv("GITHUB_COPILOT_TOKEN") or os.getenv("GITHUB_TOKEN")
    elif provider == "github":
        llm_config["model"] = os.getenv("GITHUB_MODEL", "gpt-4o")
        llm_config["api_key"] = os.getenv("GITHUB_TOKEN")

    agent = create_agent(llm_config)
    yield


app = FastAPI(title="Srečko Kosovel AI Chat", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str
    sources: list = []


class GameRoundResponse(BaseModel):
    id: int
    title: str
    category: str
    url: str | None = None
    lines: list
    words: list


def is_game_word(token):
    word = token.lower()
    return (
        WORD_RE.fullmatch(token) is not None
        and len(word) >= 4
        and word not in COMMON_WORDS
    )


def build_game_round(work):
    lines = []
    candidates = []
    seen_words = set()

    for line_index, raw_line in enumerate(work["content"].splitlines()):
        parts = []
        for token in TOKEN_RE.findall(raw_line):
            part_index = len(parts)
            parts.append({"type": "text", "text": token})
            word_key = token.lower()
            if is_game_word(token) and word_key not in seen_words:
                candidates.append((line_index, part_index, token))
                seen_words.add(word_key)
        lines.append(parts)

    if len(candidates) < GAME_BLANK_COUNT:
        return None

    selected = random.sample(candidates, GAME_BLANK_COUNT)
    words = []

    for blank_index, (line_index, part_index, word) in enumerate(selected):
        blank_id = f"blank-{work['id']}-{blank_index}"
        lines[line_index][part_index] = {
            "type": "blank",
            "blankId": blank_id,
            "answer": word,
        }
        words.append({"blankId": blank_id, "word": word})

    random.shuffle(words)

    return {
        "id": work["id"],
        "title": work["title"],
        "category": work["category_name"],
        "url": work.get("url"),
        "lines": lines,
        "words": words,
    }


def fetch_random_game_work():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, title, content, url, category_name
                FROM works_full
                WHERE category_slug = ANY(%s)
                  AND word_count >= 25
                ORDER BY RANDOM()
                LIMIT 30;
                """,
                (list(GAME_CATEGORY_SLUGS),),
            )
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    finally:
        conn.close()


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    try:
        result = agent.invoke(req.message, return_sources=True)
        return ChatResponse(answer=result["answer"], sources=result.get("sources", []))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
def health():
    return {"status": "ok", "agent_loaded": agent is not None}


@app.get("/api/game/round", response_model=GameRoundResponse)
def game_round():
    try:
        for work in fetch_random_game_work():
            round_data = build_game_round(work)
            if round_data:
                return GameRoundResponse(**round_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    raise HTTPException(status_code=404, detail="No suitable poem found")
