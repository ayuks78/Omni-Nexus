from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import Optional
import uvicorn
import os

from config import NexusConfig
from ai_engine import GmAIEngine
from rag_system import RAGSystem
from code_executor import CodeExecutor

app = FastAPI(title="Omni-Nexus @GmAI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ai_engine = GmAIEngine()
rag_system = RAGSystem()
code_executor = CodeExecutor()


class ChatRequest(BaseModel):
    message: str
    emotion_weight: Optional[float] = Field(None, ge=0.0, le=1.0)
    cognition_index: Optional[float] = Field(None, ge=0.0, le=1.0)
    mode: Optional[str] = None
    show_cot: bool = True
    use_rag: bool = True

class PersonalityUpdate(BaseModel):
    emotion_weight: float = Field(ge=0.0, le=1.0)
    cognition_index: float = Field(ge=0.0, le=1.0)

class CodeRequest(BaseModel):
    code: str
    language: str
    stdin: Optional[str] = ""

class RAGTextRequest(BaseModel):
    text: str
    title: Optional[str] = "Untitled"
    source: Optional[str] = "manual"


@app.post("/api/chat")
async def chat(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Mensagem vazia")
    rag_context = None
    if request.use_rag:
        rag_context = rag_system.query(request.message)
    result = await ai_engine.process_message(
        user_message=request.message,
        emotion_weight=request.emotion_weight,
        cognition_index=request.cognition_index,
        mode_override=request.mode,
        show_cot=request.show_cot,
        rag_context=rag_context if rag_context else None
    )
    return result

@app.delete("/api/chat/history")
async def clear_chat():
    ai_engine.clear_history()
    return {"status": "success"}

@app.get("/api/chat/stats")
async def get_stats():
    return ai_engine.get_session_stats()

@app.get("/api/personality")
async def get_personality():
    return ai_engine.personality.to_dict()

@app.put("/api/personality")
async def update_personality(update: PersonalityUpdate):
    ai_engine.personality.set_parameters(update.emotion_weight, update.cognition_index)
    return {"status": "success", "personality": ai_engine.personality.to_dict()}

@app.post("/api/code/execute")
async def execute_code(request: CodeRequest):
    return code_executor.execute(code=request.code, language=request.language, stdin=request.stdin or "")

@app.get("/api/code/history")
async def code_history():
    return {"history": code_executor.get_history()}

@app.get("/api/code/languages")
async def supported_languages():
    return {"languages": NexusConfig.SUPPORTED_LANGUAGES}

@app.post("/api/rag/upload")
async def rag_upload_file(file: UploadFile = File(...)):
    content = await file.read()
    try:
        text = content.decode("utf-8")
    except Exception:
        text = content.decode("latin-1")
    return rag_system.ingest_text(text=text, source="file_upload", title=file.filename)

@app.post("/api/rag/text")
async def rag_add_text(request: RAGTextRequest):
    return rag_system.ingest_text(text=request.text, source=request.source, title=request.title)

@app.get("/api/rag/documents")
async def rag_list_documents():
    return {"documents": rag_system.get_documents()}

@app.delete("/api/rag/documents/{doc_id}")
async def rag_delete_document(doc_id: str):
    success = rag_system.delete_document(doc_id)
    if success:
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="Not found")

@app.delete("/api/rag/clear")
async def rag_clear():
    rag_system.clear()
    return {"status": "success"}

@app.get("/api/health")
async def health():
    return {"status": "ONLINE", "system": "Omni-Nexus", "entity": "@GmAI"}


@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    html_path = os.path.join(os.path.dirname(__file__), "frontend.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()


if __name__ == "__main__":
    uvicorn.run("main:app", host=NexusConfig.HOST, port=NexusConfig.PORT, reload=False)
