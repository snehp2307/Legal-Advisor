from fastapi import FastAPI,HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from app.services.agent import ask_agent
import asyncio

app = FastAPI()

class ChatRequest(BaseModel):
    message: str

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/chat")
async def chat(req: ChatRequest):
    try:
        print("Incoming:", req.message)

        loop = asyncio.get_event_loop()

        response = await loop.run_in_executor(
            None,
            ask_agent,
            req.message
        )

        print("Response:", response)

        return {"response": response}

    except Exception as e:
        print("ERROR:", str(e))
        return {"response": f"Server error: {str(e)}"}