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
        text = content.decode('utf-8')
    except:
        text = content.decode('latin-1')
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
    raise HTTPException(status_code=404, detail="Documento nao encontrado")

@app.delete("/api/rag/clear")
async def rag_clear():
    rag_system.clear()
    return {"status": "success"}

@app.get("/api/health")
async def health():
    return {"status": "ONLINE", "system": "Omni-Nexus", "entity": "@GmAI"}


@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    return get_frontend_html()


def get_frontend_html():
    return """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>@GmAI | Omni-Nexus</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Orbitron:wght@400;700;900&family=Rajdhani:wght@400;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
<style>
:root{--g:#00ff41;--gd:#00cc33;--gg:rgba(0,255,65,.3);--gs:rgba(0,255,65,.08);--cy:#00d4ff;--rd:#ff0040;--bg1:#0a0a0f;--bg2:#0d0d14;--bg3:#12121a;--bgc:rgba(15,15,25,.85);--bgi:rgba(8,8,15,.9);--bd:rgba(0,255,65,.1);--bn:rgba(0,255,65,.2);--t1:#e0e0e0;--t2:#888;--t3:#555;--fm:'JetBrains Mono',monospace;--fd:'Orbitron',sans-serif;--fu:'Rajdhani',sans-serif;--sn:0 0 10px rgba(0,255,65,.2),0 0 20px rgba(0,255,65,.1);--ss:0 0 15px rgba(0,255,65,.4),0 0 30px rgba(0,255,65,.2)}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:var(--fu);background:var(--bg1);color:var(--t1);overflow:hidden;height:100vh}
::-webkit-scrollbar{width:5px}::-webkit-scrollbar-thumb{background:var(--gd);border-radius:3px}
::selection{background:var(--g);color:var(--bg1)}

.boot{position:fixed;inset:0;background:var(--bg1);display:flex;align-items:center;justify-content:center;z-index:9999}
.boot-c{text-align:center;width:90%;max-width:500px}
.glt{font-family:var(--fd);font-size:4rem;font-weight:900;color:var(--g);text-shadow:var(--ss);animation:gl 2s infinite}
@keyframes gl{0%,90%,100%{opacity:1}92%{opacity:.8;transform:skewX(2deg)}}
.boot-s{font-family:var(--fm);color:var(--t2);font-size:.9rem;margin:20px 0 30px;letter-spacing:3px}
.boot-p{width:100%;height:3px;background:var(--bg3);border-radius:2px;overflow:hidden;margin-bottom:20px}
.boot-pb{height:100%;width:0%;background:var(--g);box-shadow:var(--sn);transition:width .3s}
.boot-l{font-family:var(--fm);font-size:.75rem;color:var(--gd);text-align:left;height:120px;overflow:hidden;opacity:.7}
.bll{margin:2px 0;animation:fli .3s}
@keyframes fli{from{opacity:0;transform:translateX(-10px)}to{opacity:1}}

.app{display:flex;height:100vh}
.rail{width:260px;min-width:260px;height:100vh;background:var(--bg2);border-right:1px solid var(--bd);display:flex;flex-direction:column;transition:.3s;z-index:100;overflow:hidden}
.rail.clp{width:60px;min-width:60px}
.rh{display:flex;align-items:center;justify-content:space-between;padding:16px;border-bottom:1px solid var(--bd)}
.rl{display:flex;align-items:center;gap:10px}
.li{font-size:1.5rem;animation:pg 2s infinite}
@keyframes pg{0%,100%{filter:drop-shadow(0 0 5px var(--g))}50%{filter:drop-shadow(0 0 15px var(--g))}}
.lt{font-family:var(--fd);font-weight:700;font-size:1.3rem;color:var(--g);text-shadow:var(--sn)}
.rail.clp .lt,.rail.clp .ni span,.rail.clp .nl,.rail.clp .nb,.rail.clp .oi span,.rail.clp .st{display:none}
.rt{background:none;border:1px solid var(--bd);color:var(--t2);width:32px;height:32px;border-radius:6px;cursor:pointer;display:flex;align-items:center;justify-content:center}
.rt:hover{border-color:var(--g);color:var(--g)}

.rn{flex:1;overflow-y:auto;padding:12px 8px}
.ns{margin-bottom:20px}
.nl{font-family:var(--fm);font-size:.65rem;color:var(--t3);letter-spacing:2px;padding:4px 12px;display:block;margin-bottom:4px}
.ni{display:flex;align-items:center;gap:12px;width:100%;padding:10px 14px;background:transparent;border:1px solid transparent;border-radius:8px;color:var(--t2);cursor:pointer;font-family:var(--fu);font-size:.9rem;font-weight:500;transition:.15s;position:relative;text-align:left}
.ni i{width:20px;text-align:center}
.ni:hover{background:var(--gs);color:var(--t1)}
.ni.act{background:var(--gs);color:var(--g);border-color:var(--bn)}
.ni.act::before{content:'';position:absolute;left:0;top:15%;bottom:15%;width:3px;background:var(--g);border-radius:0 3px 3px 0;box-shadow:var(--sn)}
.nb{margin-left:auto;background:var(--g);color:var(--bg1);font-size:.65rem;font-weight:700;padding:1px 6px;border-radius:10px}

.rf{padding:12px 16px;border-top:1px solid var(--bd)}
.si{display:flex;align-items:center;gap:8px;margin-bottom:8px}
.sd{width:8px;height:8px;border-radius:50%;background:var(--g);box-shadow:0 0 8px var(--g);animation:pd 2s infinite}
@keyframes pd{0%,100%{opacity:1}50%{opacity:.5}}
.st{font-family:var(--fm);font-size:.7rem;color:var(--gd);letter-spacing:2px}
.oi{display:flex;align-items:center;gap:8px;color:var(--t3);font-size:.8rem}

.mc{flex:1;display:flex;flex-direction:column;height:100vh;overflow:hidden;min-width:0}
.tb{display:flex;align-items:center;justify-content:space-between;height:56px;padding:0 20px;background:var(--bg2);border-bottom:1px solid var(--bd);gap:16px;flex-shrink:0}
.tbl{display:flex;align-items:center;gap:12px}
.mmb{display:none;background:none;border:none;color:var(--t2);font-size:1.2rem;cursor:pointer;padding:8px}
.mt{font-family:var(--fd);font-size:.85rem;font-weight:600;color:var(--g);letter-spacing:2px;text-transform:uppercase;white-space:nowrap}
.mt i{margin-right:8px}
.tbr{display:flex;align-items:center;gap:12px}
.pq{display:flex;align-items:center;gap:6px}
.pl{font-family:var(--fm);font-size:.8rem;color:var(--g);font-weight:700}
.pv{font-family:var(--fm);font-size:.75rem;color:var(--t2);width:30px}

.cs{-webkit-appearance:none;height:4px;background:var(--bg3);border-radius:2px;outline:none;cursor:pointer}
.cs::-webkit-slider-thumb{-webkit-appearance:none;width:14px;height:14px;border-radius:50%;background:var(--g);box-shadow:0 0 8px var(--gg);cursor:pointer}
.cs.mn{width:60px}

.csl{background:var(--bgi);color:var(--t1);border:1px solid var(--bd);padding:6px 10px;border-radius:6px;font-family:var(--fu);font-size:.8rem;cursor:pointer;outline:none}
.csl option{background:var(--bg2)}

.bi{background:none;border:1px solid var(--bd);color:var(--t2);width:36px;height:36px;border-radius:8px;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:.15s}
.bi:hover{border-color:var(--g);color:var(--g);box-shadow:var(--sn)}

.moc{flex:1;overflow:hidden;position:relative}
.mp{position:absolute;inset:0;display:none;overflow-y:auto}
.mp.act{display:flex;flex-direction:column}

.cc{display:flex;flex-direction:column;height:100%}
.cp{background:var(--bgc);border-bottom:1px solid var(--bd);max-height:200px;overflow-y:auto}
.cph{display:flex;align-items:center;gap:8px;padding:10px 16px;font-family:var(--fm);font-size:.8rem;color:var(--cy);border-bottom:1px solid var(--bd)}
.cpc{margin-left:auto;background:none;border:none;color:var(--t3);cursor:pointer}
.cps{padding:10px 16px}
.cst{display:flex;align-items:flex-start;gap:10px;padding:6px 0;font-family:var(--fm);font-size:.75rem;color:var(--t2);border-left:2px solid var(--bd);padding-left:12px;margin-left:8px}
.cst.cmp{border-left-color:var(--g);color:var(--gd)}
.cst.prc{border-left-color:var(--cy)}
.csn{background:var(--bg3);color:var(--g);width:20px;height:20px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:.65rem;flex-shrink:0}

.cm{flex:1;overflow-y:auto;padding:20px;display:flex;flex-direction:column;gap:16px}
.wm{text-align:center;padding:60px 20px;animation:fi 1s}
@keyframes fi{from{opacity:0;transform:translateY(20px)}to{opacity:1}}
.glsm{font-family:var(--fd);font-size:2.5rem;font-weight:900;color:var(--g);text-shadow:var(--sn)}
.wt{font-family:var(--fm);font-size:1rem;color:var(--t2);margin-bottom:6px;letter-spacing:1px}
.ws{font-size:.85rem;color:var(--t3);margin-bottom:30px}
.wch{display:flex;flex-wrap:wrap;justify-content:center;gap:10px}
.ch{background:var(--bgc);border:1px solid var(--bd);color:var(--t2);padding:8px 16px;border-radius:20px;font-family:var(--fu);font-size:.85rem;cursor:pointer;transition:.15s}
.ch:hover{border-color:var(--g);color:var(--g);box-shadow:var(--sn);background:var(--gs)}

.msg{display:flex;gap:12px;max-width:85%;animation:mi .3s}
@keyframes mi{from{opacity:0;transform:translateY(10px)}to{opacity:1}}
.msg.usr{align-self:flex-end;flex-direction:row-reverse}
.msg.ast{align-self:flex-start}
.ma{width:36px;height:36px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:1rem;flex-shrink:0}
.msg.usr .ma{background:rgba(0,212,255,.15);border:1px solid rgba(0,212,255,.3);color:var(--cy)}
.msg.ast .ma{background:var(--gs);border:1px solid var(--bn);color:var(--g)}
.mco{background:var(--bgc);border:1px solid var(--bd);border-radius:12px;padding:12px 16px;min-width:60px}
.msg.usr .mco{background:rgba(0,212,255,.08);border-color:rgba(0,212,255,.2);border-bottom-right-radius:4px}
.msg.ast .mco{border-bottom-left-radius:4px}
.msn{font-family:var(--fm);font-size:.7rem;font-weight:600;margin-bottom:4px;letter-spacing:1px}
.msg.usr .msn{color:var(--cy);text-align:right}
.msg.ast .msn{color:var(--g)}
.mtx{font-size:.9rem;line-height:1.6;word-wrap:break-word}
.mtx pre{background:rgba(0,0,0,.4);border:1px solid var(--bd);border-radius:6px;padding:12px;margin:8px 0;overflow-x:auto;font-family:var(--fm);font-size:.8rem;color:var(--gd)}
.mtx code{background:rgba(0,255,65,.1);color:var(--g);padding:2px 6px;border-radius:4px;font-family:var(--fm);font-size:.85em}
.mtx strong{color:var(--g)}
.mtx em{color:var(--cy)}
.mme{font-family:var(--fm);font-size:.65rem;color:var(--t3);margin-top:6px;display:flex;gap:12px}

.ti{display:flex;gap:4px;padding:4px 0}
.td{width:6px;height:6px;background:var(--g);border-radius:50%;animation:tb 1.4s infinite}
.td:nth-child(2){animation-delay:.2s}.td:nth-child(3){animation-delay:.4s}
@keyframes tb{0%,80%,100%{transform:translateY(0);opacity:.4}40%{transform:translateY(-6px);opacity:1}}

.cia{padding:12px 20px;border-top:1px solid var(--bd);background:var(--bg2)}
.ic{display:flex;align-items:flex-end;gap:8px;background:var(--bgi);border:1px solid var(--bd);border-radius:12px;padding:8px 12px;transition:.15s}
.ic:focus-within{border-color:var(--g);box-shadow:var(--sn)}
.tp{font-family:var(--fm);font-size:.75rem;color:var(--g);font-weight:600;white-space:nowrap}
.ci{flex:1;background:transparent;border:none;color:var(--t1);font-family:var(--fu);font-size:.95rem;outline:none;resize:none;max-height:120px;line-height:1.5}
.ci::placeholder{color:var(--t3)}
.ia{display:flex;gap:4px;flex-shrink:0}
.sb{background:var(--g);color:var(--bg1);border:none;width:36px;height:36px;border-radius:8px;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:.15s;font-size:.9rem}
.sb:hover{box-shadow:var(--ss);transform:scale(1.05)}

.cec{display:flex;flex-direction:column;height:100%;padding:16px;gap:12px}
.etb{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.cb{background:var(--g);color:var(--bg1);border:none;padding:8px 16px;border-radius:6px;font-family:var(--fu);font-weight:600;font-size:.85rem;cursor:pointer;display:flex;align-items:center;gap:6px;transition:.15s}
.cb:hover{box-shadow:var(--ss);transform:translateY(-1px)}
.cb.sec{background:transparent;color:var(--g);border:1px solid var(--g)}
.cb.sm{padding:4px 10px;font-size:.75rem}
.cb.dng{background:transparent;color:var(--rd);border:1px solid var(--rd)}

.eb{flex:1;display:grid;grid-template-columns:1fr 1fr;gap:12px;min-height:0}
.ep,.op{display:flex;flex-direction:column;background:var(--bgc);border:1px solid var(--bd);border-radius:8px;overflow:hidden}
.ph{display:flex;align-items:center;gap:8px;padding:8px 14px;background:var(--bg3);border-bottom:1px solid var(--bd);font-family:var(--fm);font-size:.75rem;color:var(--gd);letter-spacing:1px}
.et{margin-left:auto;color:var(--cy)}
.ep{position:relative}
.ln{position:absolute;left:0;top:38px;bottom:0;width:40px;background:var(--bg3);border-right:1px solid var(--bd);padding:12px 4px;font-family:var(--fm);font-size:.75rem;color:var(--t3);text-align:right;line-height:1.5;overflow:hidden;user-select:none}
.ct{flex:1;background:transparent;color:var(--g);border:none;padding:12px 12px 12px 48px;font-family:var(--fm);font-size:.85rem;line-height:1.5;resize:none;outline:none;tab-size:4;white-space:pre;overflow:auto}
.ct::placeholder{color:var(--t3)}
.co{flex:1;padding:12px;font-family:var(--fm);font-size:.8rem;color:var(--t1);overflow:auto;margin:0;line-height:1.5;white-space:pre-wrap}
.co.err{color:var(--rd)}.co.suc{color:var(--g)}
.sic{display:flex;gap:8px;align-items:flex-start}
.sil{font-family:var(--fm);font-size:.75rem;color:var(--t3);white-space:nowrap;padding-top:8px}
.sit{flex:1;background:var(--bgi);border:1px solid var(--bd);border-radius:6px;padding:8px 12px;color:var(--t1);font-family:var(--fm);font-size:.8rem;outline:none;resize:none}

.rc{padding:20px;display:flex;flex-direction:column;gap:20px}
.rhs h2{font-family:var(--fd);font-size:1.1rem;color:var(--g);margin-bottom:6px}
.rdesc{font-size:.85rem;color:var(--t2)}
.ruz{border:2px dashed var(--bn);border-radius:12px;padding:40px 20px;text-align:center;cursor:pointer;transition:.15s}
.ruz:hover{border-color:var(--g);background:var(--gs)}
.ui{font-size:2.5rem;color:var(--gd);margin-bottom:12px}
.ruz p{color:var(--t2);margin-bottom:6px}
.uf{font-size:.75rem;color:var(--t3)}
.rti{background:var(--bgc);border:1px solid var(--bd);border-radius:10px;padding:16px;display:flex;flex-direction:column;gap:10px}
.rti h3{font-family:var(--fd);font-size:.85rem;color:var(--g)}
.cin{background:var(--bgi);border:1px solid var(--bd);border-radius:6px;padding:10px 14px;color:var(--t1);font-family:var(--fu);font-size:.9rem;outline:none;width:100%}
.cin:focus{border-color:var(--g)}
.cta{background:var(--bgi);border:1px solid var(--bd);border-radius:6px;padding:10px 14px;color:var(--t1);font-family:var(--fm);font-size:.85rem;resize:vertical;outline:none;width:100%}
.rd h3{font-family:var(--fd);font-size:.85rem;color:var(--g);display:flex;align-items:center;justify-content:space-between;margin-bottom:12px}
.dl{display:flex;flex-direction:column;gap:8px}
.di{display:flex;align-items:center;gap:12px;background:var(--bgc);border:1px solid var(--bd);border-radius:8px;padding:12px}
.dic{color:var(--g);font-size:1.2rem}
.dif{flex:1}.dit{font-weight:600;font-size:.9rem}.dim{font-size:.75rem;color:var(--t3)}
.did{background:none;border:none;color:var(--t3);cursor:pointer;padding:6px}.did:hover{color:var(--rd)}
.es{color:var(--t3);font-style:italic;text-align:center;padding:20px}

.pc{padding:20px;display:flex;flex-direction:column;gap:20px}
.pch h2{font-family:var(--fd);font-size:1.1rem;color:var(--g);margin-bottom:6px}
.pch p{color:var(--t2);font-size:.85rem}
.ccd{background:var(--bgc);border:1px solid var(--bd);border-radius:10px;padding:20px;margin-bottom:16px}
.ccdh{display:flex;align-items:center;justify-content:space-between;margin-bottom:6px}
.ccdh h3{font-family:var(--fd);font-size:.85rem;color:var(--g)}
.ccv{font-family:var(--fm);font-size:1.2rem;font-weight:700;color:var(--g);text-shadow:var(--sn)}
.ccds{font-size:.8rem;color:var(--t3);margin-bottom:14px}
.ces{width:100%;height:6px;-webkit-appearance:none;background:var(--bg3);border-radius:3px;outline:none;cursor:pointer}
.ces::-webkit-slider-thumb{-webkit-appearance:none;width:20px;height:20px;border-radius:50%;background:var(--g);box-shadow:0 0 8px var(--gg);cursor:pointer}
.ccs{width:100%;height:6px;-webkit-appearance:none;background:var(--bg3);border-radius:3px;outline:none;cursor:pointer}
.ccs::-webkit-slider-thumb{-webkit-appearance:none;width:20px;height:20px;border-radius:50%;background:var(--cy);box-shadow:0 0 8px rgba(0,212,255,.4);cursor:pointer}
.ccl{display:flex;justify-content:space-between;font-size:.7rem;color:var(--t3);margin-top:8px}
.pg{display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:10px;margin-top:12px}
.pb{background:rgba(10,10,18,.75);border:1px solid var(--bd);border-radius:10px;padding:14px;text-align:center;cursor:pointer;transition:.15s;color:var(--t2);display:flex;flex-direction:column;align-items:center;gap:6px}
.pb i{font-size:1.3rem}.pb span{font-size:.8rem;font-weight:600}.pb small{font-family:var(--fm);font-size:.65rem;color:var(--t3)}
.pb:hover{border-color:var(--g);color:var(--g)}
.pb.act{border-color:var(--g);background:var(--gs);color:var(--g);box-shadow:var(--sn)}
.nsc{background:var(--bgc);border:1px solid var(--bd);border-radius:10px;padding:20px}
.nsc h3{font-family:var(--fd);font-size:.85rem;color:var(--g);margin-bottom:16px}
.sg{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px}
.sti{background:rgba(10,10,18,.75);border:1px solid var(--bd);border-radius:8px;padding:12px;text-align:center}
.stl{font-size:.7rem;color:var(--t3);margin-bottom:4px;display:block}
.stv{font-family:var(--fm);font-weight:700;font-size:.9rem;color:var(--t1)}
.stv.ne{color:var(--g);text-shadow:var(--sn)}

.sc{padding:20px}
.sc h2{font-family:var(--fd);font-size:1.1rem;color:var(--g);margin-bottom:20px}
.stg{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:14px;margin-bottom:20px}
.stc{background:var(--bgc);border:1px solid var(--bd);border-radius:10px;padding:20px;text-align:center;transition:.15s}
.stc:hover{border-color:var(--bn);transform:translateY(-2px);box-shadow:var(--sn)}
.stci{font-size:1.5rem;color:var(--g);margin-bottom:10px}
.stcv{font-family:var(--fm);font-size:1.5rem;font-weight:700;color:var(--g);text-shadow:var(--sn)}
.stcl{font-size:.75rem;color:var(--t3);margin-top:4px}

.mo{display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:999}.mo.act{display:block}
@media(max-width:900px){.rail{position:fixed;left:-260px;transition:left .3s;z-index:1000;box-shadow:5px 0 30px rgba(0,0,0,.5)}.rail.mop{left:0}.mmb{display:flex!important}.pq{display:none!important}.eb{grid-template-columns:1fr}.msg{max-width:95%}}
@media(max-width:600px){.mt{font-size:.7rem}.ms{display:none}.wch{flex-direction:column}.stg{grid-template-columns:repeat(2,1fr)}}
</style>
</head>
<body>
<div id="bs" class="boot"><div class="boot-c"><div><span class="glt" data-text="@GmAI">@GmAI</span></div><div class="boot-s">OMNI-NEXUS PROTOCOL v1.0</div><div class="boot-p"><div class="boot-pb" id="bpb"></div></div><div class="boot-l" id="bl"></div></div></div>
<div id="app" class="app" style="display:none">
<aside id="rail" class="rail"><div class="rh"><div class="rl"><span class="li">⚡</span><span class="lt">GmAI</span></div><button class="rt" id="rtb"><i class="fas fa-bars"></i></button></div>
<nav class="rn"><div class="ns"><span class="nl">MODULOS NEURAIS</span><button class="ni act" data-m="chat"><i class="fas fa-brain"></i><span>Neural Chat</span><span class="nb" id="cbg">0</span></button><button class="ni" data-m="code"><i class="fas fa-code"></i><span>Code Terminal</span></button><button class="ni" data-m="rag"><i class="fas fa-database"></i><span>RAG Memory</span></button><button class="ni" data-m="cot"><i class="fas fa-project-diagram"></i><span>Thought Tree</span></button></div>
<div class="ns"><span class="nl">CONFIG</span><button class="ni" data-m="pers"><i class="fas fa-sliders-h"></i><span>Neural Config</span></button><button class="ni" data-m="stats"><i class="fas fa-chart-bar"></i><span>System Stats</span></button></div></nav>
<div class="rf"><div class="si"><span class="sd"></span><span class="st">ONLINE</span></div><div class="oi"><i class="fas fa-user-secret"></i><span>@ayuks78</span></div></div></aside>

<main class="mc"><header class="tb"><div class="tbl"><button class="mmb" id="mmb"><i class="fas fa-bars"></i></button><h1 class="mt" id="mtl"><i class="fas fa-brain"></i> Neural Chat</h1></div>
<div class="tbr"><div class="pq"><span class="pl">e</span><input type="range" id="qe" min="0" max="100" value="50" class="cs mn"><span class="pv" id="qev">0.50</span></div>
<div class="pq"><span class="pl">k</span><input type="range" id="qc" min="0" max="100" value="80" class="cs mn"><span class="pv" id="qcv">0.80</span></div>
<div class="ms"><select id="msl" class="csl"><option value="balanced">Balanceado</option><option value="cold_logic">Logica Fria</option><option value="empathic">Empatico</option><option value="hacker">Hacker</option></select></div>
<button class="bi" id="ccb" title="Limpar"><i class="fas fa-trash-alt"></i></button></div></header>

<div class="moc">
<div class="mp act" id="p-chat"><div class="cc">
<div class="cp" id="cpp" style="display:none"><div class="cph"><i class="fas fa-brain"></i> Chain of Thought<button class="cpc" id="cpcl"><i class="fas fa-times"></i></button></div><div class="cps" id="cpst"></div></div>
<div class="cm" id="cms"><div class="wm"><div><span class="glsm">@GmAI</span></div><p class="wt">Protocolo Omni-Nexus Inicializado</p><p class="ws">Operador @ayuks78 conectado.</p><div class="wch"><button class="ch" onclick="sqm('Ola GmAI, quem e voce?')">👋 Ola</button><button class="ch" onclick="sqm('Crie um script Python')">🐍 Python</button><button class="ch" onclick="sqm('Seguranca cibernetica')">🔒 Security</button><button class="ch" onclick="sqm('Resolva x^2+5x+6=0')">🧮 Math</button></div></div></div>
<div class="cia"><div class="ic"><div><span class="tp">@ayuks78 ▸</span></div><textarea id="cin" class="ci" placeholder="Digite sua mensagem..." rows="1"></textarea><div class="ia"><button class="bi" id="cotb" title="CoT"><i class="fas fa-project-diagram"></i></button><button class="sb" id="snb"><i class="fas fa-paper-plane"></i></button></div></div></div>
</div></div>

<div class="mp" id="p-code"><div class="cec"><div class="etb"><select id="cdl" class="csl"><option value="python">Python</option><option value="javascript">JavaScript</option><option value="html">HTML</option><option value="css">CSS</option></select><button class="cb" id="rnb"><i class="fas fa-play"></i> EXECUTAR</button><button class="cb sec" id="clcb"><i class="fas fa-eraser"></i> LIMPAR</button><button class="cb sec" id="aib"><i class="fas fa-robot"></i> AI ASSIST</button></div>
<div class="eb"><div class="ep"><div class="ph"><i class="fas fa-edit"></i> EDITOR</div><div class="ln" id="lns">1</div><textarea id="cdi" class="ct" spellcheck="false" placeholder="# Seu codigo aqui..."></textarea></div><div class="op"><div class="ph"><i class="fas fa-terminal"></i> OUTPUT<span class="et" id="ext"></span></div><pre class="co" id="cdo">Aguardando...</pre></div></div>
<div class="sic"><label class="sil"><i class="fas fa-keyboard"></i> STDIN:</label><textarea id="sdi" class="sit" placeholder="Input..." rows="2"></textarea></div></div></div>

<div class="mp" id="p-rag"><div class="rc"><div class="rhs"><h2><i class="fas fa-database"></i> RAG Memory</h2><p class="rdesc">Upload de documentos</p></div>
<div class="ruz" id="ruz"><div class="ui"><i class="fas fa-cloud-upload-alt"></i></div><p>Clique para upload</p><p class="uf">.txt .md .py .js .json</p><input type="file" id="rfi" style="display:none" accept=".txt,.md,.py,.js,.json,.csv" multiple></div>
<div class="rti"><h3><i class="fas fa-pen"></i> Texto Manual</h3><input type="text" id="rtt" class="cin" placeholder="Titulo..."><textarea id="rtx" class="cta" placeholder="Conteudo..." rows="4"></textarea><button class="cb" id="ratb"><i class="fas fa-plus"></i> ADICIONAR</button></div>
<div class="rd"><h3><i class="fas fa-folder-open"></i> Documentos <button class="cb sm dng" id="rcab"><i class="fas fa-trash"></i> Limpar</button></h3><div class="dl" id="rdl"><p class="es">Nenhum documento</p></div></div></div></div>

<div class="mp" id="p-cot"><div style="padding:20px"><h2 style="font-family:var(--fd);color:var(--g);margin-bottom:10px"><i class="fas fa-project-diagram"></i> Thought Tree</h2><p style="color:var(--t2);margin-bottom:20px">Raciocinio em tempo real</p><div id="ttv" style="background:var(--bgc);border:1px solid var(--bd);border-radius:10px;min-height:300px;padding:20px"><div class="es"><i class="fas fa-brain" style="font-size:3rem;opacity:.3;display:block;margin-bottom:12px"></i>Envie mensagem para ver raciocinio</div></div></div></div>

<div class="mp" id="p-pers"><div class="pc"><div class="pch"><h2><i class="fas fa-sliders-h"></i> Modulacao Neuronal</h2><p>Controle total da @GmAI</p></div>
<div class="ccd"><div class="ccdh"><h3>Peso Emocional (e)</h3><span class="ccv" id="edsp">0.50</span></div><div class="ccds">0%=Logica Fria / 100%=Empatia</div><input type="range" id="esl" min="0" max="100" value="50" class="ces"><div class="ccl"><span>🧊 FRIO</span><span>⚖️ NEUTRO</span><span>💚 EMPATICO</span></div></div>
<div class="ccd"><div class="ccdh"><h3>Indice Cognicao (k)</h3><span class="ccv" id="cdsp">0.80</span></div><div class="ccds">Profundidade do raciocinio</div><input type="range" id="csl2" min="0" max="100" value="80" class="ccs"><div class="ccl"><span>⚡ RAPIDO</span><span>🔍 NORMAL</span><span>🧠 PROFUNDO</span></div></div>
<div class="ccd"><h3>Presets</h3><div class="pg"><button class="pb" data-e="0" data-c="100" data-md="cold_logic"><i class="fas fa-snowflake"></i><span>Logica Fria</span><small>e=0 k=1.0</small></button><button class="pb act" data-e="50" data-c="80" data-md="balanced"><i class="fas fa-balance-scale"></i><span>Balanceado</span><small>e=0.5 k=0.8</small></button><button class="pb" data-e="100" data-c="70" data-md="empathic"><i class="fas fa-heart"></i><span>Empatico</span><small>e=1.0 k=0.7</small></button><button class="pb" data-e="20" data-c="95" data-md="hacker"><i class="fas fa-skull-crossbones"></i><span>Hacker</span><small>e=0.2 k=0.95</small></button></div></div>
<div class="nsc"><h3><i class="fas fa-heartbeat"></i> Status Neural</h3><div class="sg"><div class="sti"><span class="stl">Modo</span><span class="stv ne" id="amd">BALANCED</span></div><div class="sti"><span class="stl">CoT</span><span class="stv" id="cotsd">ATIVO</span></div><div class="sti"><span class="stl">Profundidade</span><span class="stv" id="dpd">MAXIMA</span></div><div class="sti"><span class="stl">Interacoes</span><span class="stv" id="intd">0</span></div></div></div></div></div>

<div class="mp" id="p-stats"><div class="sc"><h2><i class="fas fa-chart-bar"></i> System Stats</h2><div class="stg">
<div class="stc"><div class="stci"><i class="fas fa-comments"></i></div><div class="stcv" id="s-int">0</div><div class="stcl">Interacoes</div></div>
<div class="stc"><div class="stci"><i class="fas fa-clock"></i></div><div class="stcv" id="s-up">0s</div><div class="stcl">Uptime</div></div>
<div class="stc"><div class="stci"><i class="fas fa-memory"></i></div><div class="stcv" id="s-ctx">0</div><div class="stcl">Contexto</div></div>
<div class="stc"><div class="stci"><i class="fas fa-fingerprint"></i></div><div class="stcv" id="s-unq">0</div><div class="stcl">Unicas</div></div>
<div class="stc"><div class="stci"><i class="fas fa-file-alt"></i></div><div class="stcv" id="s-rag">0</div><div class="stcl">Docs RAG</div></div>
<div class="stc"><div class="stci"><i class="fas fa-terminal"></i></div><div class="stcv" id="s-exe">0</div><div class="stcl">Execucoes</div></div>
</div><button class="cb" id="rsb"><i class="fas fa-sync-alt"></i> ATUALIZAR</button></div></div>
</div></main></div>

<script>
const AB=window.location.origin;
const S={mod:'chat',cot:true,proc:false,ch:[],coth:[],p:{ew:.5,ci:.8,m:'balanced'},mc:0,so:false};

function boot(){const l=document.getElementById('bl'),p=document.getElementById('bpb'),m=['[INIT] Omni-Nexus v1.0...','[CORE] Neural Engine...','[SYNC] LLM Connect...','[AUTH] @ayuks78 OK','[LOAD] CoT... OK','[LOAD] RAG... OK','[LOAD] Code Exec... OK','[AI] @GmAI... READY','','⚡ ONLINE ⚡'];let i=0;const iv=3000/m.length;const bi=setInterval(()=>{if(i<m.length){const d=document.createElement('div');d.className='bll';d.textContent=m[i];l.appendChild(d);l.scrollTop=l.scrollHeight;p.style.width=((i+1)/m.length*100)+'%';i++}else{clearInterval(bi);setTimeout(()=>{document.getElementById('bs').style.opacity='0';setTimeout(()=>{document.getElementById('bs').style.display='none';document.getElementById('app').style.display='flex';init()},500)},500)}},iv)}

function init(){sNav();sChat();sCode();sRAG();sPers();sQC();sMM();lSt()}

function sNav(){document.querySelectorAll('.ni[data-m]').forEach(i=>{i.addEventListener('click',()=>{sw(i.dataset.m);if(S.so)tMM()})});document.getElementById('rtb').addEventListener('click',()=>{document.getElementById('rail').classList.toggle('clp')})}

function sw(n){S.mod=n;document.querySelectorAll('.ni').forEach(i=>i.classList.toggle('act',i.dataset.m===n));document.querySelectorAll('.mp').forEach(p=>p.classList.remove('act'));const p=document.getElementById('p-'+n);if(p)p.classList.add('act');const t={chat:'<i class="fas fa-brain"></i> Neural Chat',code:'<i class="fas fa-code"></i> Code Terminal',rag:'<i class="fas fa-database"></i> RAG Memory',cot:'<i class="fas fa-project-diagram"></i> Thought Tree',pers:'<i class="fas fa-sliders-h"></i> Neural Config',stats:'<i class="fas fa-chart-bar"></i> System Stats'};document.getElementById('mtl').innerHTML=t[n]||n;if(n==='stats')lSt();if(n==='rag')lRD()}

function sMM(){document.getElementById('mmb').addEventListener('click',tMM);const o=document.createElement('div');o.className='mo';o.id='mmo';o.addEventListener('click',tMM);document.body.appendChild(o)}
function tMM(){S.so=!S.so;document.getElementById('rail').classList.toggle('mop',S.so);document.getElementById('mmo').classList.toggle('act',S.so)}

function sChat(){const i=document.getElementById('cin'),s=document.getElementById('snb'),c=document.getElementById('ccb'),ct=document.getElementById('cotb'),cc=document.getElementById('cpcl');
s.addEventListener('click',sMsg);i.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();sMsg()}});i.addEventListener('input',()=>{i.style.height='auto';i.style.height=Math.min(i.scrollHeight,120)+'px'});
c.addEventListener('click',async()=>{if(confirm('Limpar chat?')){try{await fetch(AB+'/api/chat/history',{method:'DELETE'})}catch(e){}document.getElementById('cms').innerHTML=wHTML();S.ch=[];S.mc=0;uBdg()}});
ct.addEventListener('click',()=>{S.cot=!S.cot;ct.style.color=S.cot?'var(--g)':'';ct.style.borderColor=S.cot?'var(--g)':''});
cc.addEventListener('click',()=>{document.getElementById('cpp').style.display='none'})}

async function sMsg(){const i=document.getElementById('cin'),m=i.value.trim();if(!m||S.proc)return;S.proc=true;i.value='';i.style.height='auto';const w=document.querySelector('.wm');if(w)w.remove();aMsg('usr',m);const tid=sTI();if(S.cot)sCP();
try{const r=await fetch(AB+'/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:m,emotion_weight:S.p.ew,cognition_index:S.p.ci,mode:S.p.m,show_cot:S.cot,use_rag:true})});const d=await r.json();rTI(tid);if(d.chain_of_thought&&S.cot){uCD(d.chain_of_thought);S.coth.push({q:m,s:d.chain_of_thought,t:Date.now()});uTTV()}aMsg('ast',d.response,d.metadata)}catch(e){rTI(tid);aMsg('ast','Error: '+e.message)}S.proc=false;S.mc++;uBdg()}

function sqm(t){document.getElementById('cin').value=t;sMsg()}
window.sqm=sqm;

function aMsg(r,c,meta=null){const ct=document.getElementById('cms'),d=document.createElement('div');d.className='msg '+(r==='usr'?'usr':'ast');const av=r==='usr'?'👤':'⚡',sn=r==='usr'?'@ayuks78':'@GmAI',fc=fMsg(c);let mh='';if(meta)mh='<div class="mme"><span>⏱️ '+meta.processing_time_ms+'ms</span><span>💬 #'+meta.context_turns+'</span></div>';d.innerHTML='<div class="ma">'+av+'</div><div class="mco"><div class="msn">'+sn+'</div><div class="mtx">'+fc+'</div>'+mh+'</div>';ct.appendChild(d);ct.scrollTop=ct.scrollHeight}

function fMsg(t){if(!t)return'';let f=t.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');f=f.replace(/```(\\w*)\\n?([\\s\\S]*?)```/g,(m,l,c)=>'<pre><code>'+c.trim()+'</code></pre>');f=f.replace(/`([^`]+)`/g,'<code>$1</code>');f=f.replace(/\\*\\*([^*]+)\\*\\*/g,'<strong>$1</strong>');f=f.replace(/\\*([^*]+)\\*/g,'<em>$1</em>');f=f.replace(/\\n/g,'<br>');return f}

function sTI(){const c=document.getElementById('cms'),id='t'+Date.now(),d=document.createElement('div');d.className='msg ast';d.id=id;d.innerHTML='<div class="ma">⚡</div><div class="mco"><div class="msn">@GmAI</div><div class="ti"><div class="td"></div><div class="td"></div><div class="td"></div></div></div>';c.appendChild(d);c.scrollTop=c.scrollHeight;return id}
function rTI(id){const e=document.getElementById(id);if(e)e.remove()}
function uBdg(){const b=document.getElementById('cbg');if(b)b.textContent=S.mc}
function wHTML(){return '<div class="wm"><div><span class="glsm">@GmAI</span></div><p class="wt">Protocolo Omni-Nexus</p><p class="ws">@ayuks78 conectado.</p><div class="wch"><button class="ch" onclick="sqm(\'Ola GmAI\')">👋 Ola</button><button class="ch" onclick="sqm(\'Script Python\')">🐍 Python</button></div></div>'}

function sCP(){const p=document.getElementById('cpp'),s=document.getElementById('cpst');p.style.display='block';s.innerHTML='<div class="cst prc"><span class="csn">1</span><div>Processando...</div></div>'}
function uCD(steps){document.getElementById('cpst').innerHTML=steps.map(s=>'<div class="cst cmp"><span class="csn">'+s.step+'</span><div><div style="color:var(--g);font-weight:600;font-size:.75rem">'+s.title+'</div><div style="font-size:.7rem">'+s.content+'</div></div></div>').join('')}
function uTTV(){const v=document.getElementById('ttv');if(!S.coth.length)return;const l=S.coth[S.coth.length-1];v.innerHTML='<div style="font-family:var(--fm);font-size:.8rem;color:var(--cy);margin-bottom:12px">Query: "'+l.q.substring(0,80)+'"</div>'+l.s.map(s=>'<div style="background:rgba(10,10,18,.75);border:1px solid var(--bn);border-radius:8px;padding:10px 14px;margin:8px 0 8px 24px;font-family:var(--fm);font-size:.8rem"><div style="font-weight:700;color:var(--g);font-size:.75rem;margin-bottom:4px">Passo '+s.step+': '+s.title+'</div><div>'+s.content+'</div></div>').join('')}

function sCode(){const c=document.getElementById('cdi'),r=document.getElementById('rnb'),cl=document.getElementById('clcb'),ai=document.getElementById('aib');
r.addEventListener('click',exCode);cl.addEventListener('click',()=>{c.value='';document.getElementById('cdo').textContent='Aguardando...';document.getElementById('cdo').className='co';document.getElementById('ext').textContent='';uLN()});
ai.addEventListener('click',()=>{const code=c.value.trim();if(!code)return;sw('chat');document.getElementById('cin').value='Analise: ```'+document.getElementById('cdl').value+'\\n'+code+'\\n```';sMsg()});
c.addEventListener('input',uLN);c.addEventListener('keydown',e=>{if(e.key==='Tab'){e.preventDefault();const s=c.selectionStart,en=c.selectionEnd;c.value=c.value.substring(0,s)+'    '+c.value.substring(en);c.selectionStart=c.selectionEnd=s+4;uLN()}if(e.key==='Enter'&&e.ctrlKey){e.preventDefault();exCode()}});uLN()}

function uLN(){const c=document.getElementById('cdi'),l=document.getElementById('lns'),n=c.value.split('\\n').length;l.textContent=Array.from({length:Math.max(n,1)},(_,i)=>i+1).join('\\n')}

async function exCode(){const code=document.getElementById('cdi').value,lang=document.getElementById('cdl').value,stdin=document.getElementById('sdi').value,out=document.getElementById('cdo'),et=document.getElementById('ext');if(!code.trim()){out.textContent='Nenhum codigo';out.className='co err';return}out.textContent='Executando...';out.className='co';et.textContent='';
try{const r=await fetch(AB+'/api/code/execute',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({code,language:lang,stdin})});const d=await r.json();out.textContent=d.success?(d.output||'OK (sem output)'):(d.output?d.output+'\\n\\n':'')+'ERRO:\\n'+d.error;out.className='co '+(d.success?'suc':'err');et.textContent=d.execution_time+'ms'}catch(e){out.textContent='Erro: '+e.message;out.className='co err'}}

function sRAG(){const uz=document.getElementById('ruz'),fi=document.getElementById('rfi'),at=document.getElementById('ratb'),ca=document.getElementById('rcab');
uz.addEventListener('click',()=>fi.click());uz.addEventListener('dragover',e=>{e.preventDefault();uz.style.borderColor='var(--g)'});uz.addEventListener('dragleave',()=>{uz.style.borderColor=''});uz.addEventListener('drop',e=>{e.preventDefault();uz.style.borderColor='';hRF(e.dataTransfer.files)});fi.addEventListener('change',e=>hRF(e.target.files));at.addEventListener('click',aRT);ca.addEventListener('click',async()=>{if(confirm('Limpar RAG?')){try{await fetch(AB+'/api/rag/clear',{method:'DELETE'});lRD()}catch(e){}}})}

async function hRF(files){for(const f of files){const fd=new FormData();fd.append('file',f);try{await fetch(AB+'/api/rag/upload',{method:'POST',body:fd})}catch(e){}}lRD()}

async function aRT(){const t=document.getElementById('rtt').value.trim()||'Untitled',x=document.getElementById('rtx').value.trim();if(!x)return;try{await fetch(AB+'/api/rag/text',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:x,title:t,source:'manual'})});document.getElementById('rtt').value='';document.getElementById('rtx').value='';lRD()}catch(e){}}

async function lRD(){const l=document.getElementById('rdl');try{const r=await fetch(AB+'/api/rag/documents'),d=await r.json();if(!d.documents||!d.documents.length){l.innerHTML='<p class="es">Nenhum documento</p>';return}l.innerHTML=d.documents.map(doc=>'<div class="di"><div class="dic"><i class="fas fa-file-alt"></i></div><div class="dif"><div class="dit">'+(doc.metadata?.title||doc.id)+'</div><div class="dim">'+doc.chunks+' chunks</div></div><button class="did" onclick="dRD(\''+doc.id+'\')"><i class="fas fa-trash"></i></button></div>').join('')}catch(e){l.innerHTML='<p class="es">Erro</p>'}}

async function dRD(id){try{await fetch(AB+'/api/rag/documents/'+id,{method:'DELETE'});lRD()}catch(e){}}
window.dRD=dRD;

function sPers(){const es=document.getElementById('esl'),cs=document.getElementById('csl2');
es.addEventListener('input',()=>{const v=es.value/100;S.p.ew=v;document.getElementById('edsp').textContent=v.toFixed(2);document.getElementById('qe').value=es.value;document.getElementById('qev').textContent=v.toFixed(2);uMFS();sP()});
cs.addEventListener('input',()=>{const v=cs.value/100;S.p.ci=v;document.getElementById('cdsp').textContent=v.toFixed(2);document.getElementById('qc').value=cs.value;document.getElementById('qcv').textContent=v.toFixed(2);uNS();sP()});
document.querySelectorAll('.pb').forEach(b=>{b.addEventListener('click',()=>{const e=parseInt(b.dataset.e),c=parseInt(b.dataset.c),m=b.dataset.md;es.value=e;cs.value=c;S.p.ew=e/100;S.p.ci=c/100;S.p.m=m;document.getElementById('edsp').textContent=(e/100).toFixed(2);document.getElementById('cdsp').textContent=(c/100).toFixed(2);document.getElementById('qe').value=e;document.getElementById('qc').value=c;document.getElementById('qev').textContent=(e/100).toFixed(2);document.getElementById('qcv').textContent=(c/100).toFixed(2);document.getElementById('msl').value=m;document.querySelectorAll('.pb').forEach(x=>x.classList.remove('act'));b.classList.add('act');uNS();sP()})});
document.getElementById('msl').addEventListener('change',e=>{S.p.m=e.target.value})}

function sQC(){document.getElementById('qe').addEventListener('input',function(){const v=this.value/100;S.p.ew=v;document.getElementById('qev').textContent=v.toFixed(2);document.getElementById('esl').value=this.value;document.getElementById('edsp').textContent=v.toFixed(2);uMFS()});document.getElementById('qc').addEventListener('input',function(){const v=this.value/100;S.p.ci=v;document.getElementById('qcv').textContent=v.toFixed(2);document.getElementById('csl2').value=this.value;document.getElementById('cdsp').textContent=v.toFixed(2);uNS()})}

function uMFS(){const e=S.p.ew;let m='balanced';if(e<.2)m='cold_logic';else if(e>.8)m='empathic';S.p.m=m;document.getElementById('msl').value=m;document.querySelectorAll('.pb').forEach(b=>b.classList.toggle('act',b.dataset.md===m));uNS()}

function uNS(){const c=S.p.ci;const mn={cold_logic:'LOGICA FRIA',balanced:'BALANCEADO',empathic:'EMPATICO',hacker:'HACKER'};const a=document.getElementById('amd'),ct=document.getElementById('cotsd'),d=document.getElementById('dpd');if(a)a.textContent=mn[S.p.m]||'BALANCEADO';if(ct)ct.textContent=c>.5?'ATIVO':'PASSIVO';if(d)d.textContent=c>.7?'MAXIMA':'PADRAO'}

async function sP(){try{await fetch(AB+'/api/personality',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({emotion_weight:S.p.ew,cognition_index:S.p.ci})})}catch(e){}}

async function lSt(){try{const r=await fetch(AB+'/api/chat/stats'),d=await r.json();document.getElementById('s-int').textContent=d.session_metadata?.total_interactions||0;document.getElementById('s-ctx').textContent=d.history_length||0;document.getElementById('s-unq').textContent=d.unique_responses||0;document.getElementById('intd').textContent=d.session_metadata?.total_interactions||0;const u=d.uptime_seconds||0;document.getElementById('s-up').textContent=u<60?Math.round(u)+'s':Math.round(u/60)+'m'}catch(e){}try{const r=await fetch(AB+'/api/rag/documents'),d=await r.json();document.getElementById('s-rag').textContent=d.documents?.length||0}catch(e){}try{const r=await fetch(AB+'/api/code/history'),d=await r.json();document.getElementById('s-exe').textContent=d.history?.length||0}catch(e){}const rb=document.getElementById('rsb');if(rb&&!rb.hl){rb.addEventListener('click',lSt);rb.hl=true}}

document.addEventListener('DOMContentLoaded',boot);
</script>
</body></html>"""


if __name__ == "__main__":
    print("GmAI Omni-Nexus Starting...")
    uvicorn.run("main:app", host=NexusConfig.HOST, port=NexusConfig.PORT, reload=False)
