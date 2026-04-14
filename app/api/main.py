import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.services.agent import ask_agent

MAX_WORKERS      = 8        
AGENT_TIMEOUT    = 90        

_executor = ThreadPoolExecutor(max_workers=MAX_WORKERS, thread_name_prefix="lexai")

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


@app.on_event("shutdown")
async def shutdown_event():
    """Gracefully drain in-flight requests on shutdown."""
    _executor.shutdown(wait=True)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "pool_max_workers": MAX_WORKERS,
    }


@app.post("/chat")
async def chat(req: ChatRequest):
    try:
        print(f"[chat] incoming: {req.message[:60]!r}")
        loop = asyncio.get_event_loop()

        # asyncio.wait_for enforces a hard deadline even if the thread hangs
        response = await asyncio.wait_for(
            loop.run_in_executor(_executor, ask_agent, req.message),
            timeout=AGENT_TIMEOUT,
        )

        print(f"[chat] response length: {len(response)}")
        return {"response": response}

    except asyncio.TimeoutError:
        print(f"[chat] TIMEOUT after {AGENT_TIMEOUT}s for: {req.message[:60]!r}")
        raise HTTPException(
            status_code=504,
            detail=f"Agent timed out after {AGENT_TIMEOUT}s. Try a shorter query.",
        )

    except Exception as e:
        print(f"[chat] ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))