import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.db.models import create_tables

from app.services.agent import ask_agent
create_tables()
AGENT_TIMEOUT = 90

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat")
async def chat(req: ChatRequest):
    try:
        print(f"[chat] incoming: {req.message[:60]!r}")

        response = await asyncio.wait_for(
            ask_agent(req.message),
            timeout=AGENT_TIMEOUT,
        )

        print(f"[chat] response length: {len(response)}")
        return {"response": response}

    except asyncio.TimeoutError:
        print(f"[chat] TIMEOUT after {AGENT_TIMEOUT}s")
        raise HTTPException(
            status_code=504,
            detail=f"Agent timed out after {AGENT_TIMEOUT}s",
        )

    except Exception as e:
        print(f"[chat] ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
