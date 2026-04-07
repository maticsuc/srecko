"""
FastAPI backend for the Srečko Kosovel AI Chat.

Endpoints:
    POST /api/chat   — send a message, get Srečko's response
    GET  /api/health  — liveness check
"""

import os
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

agent = None


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
