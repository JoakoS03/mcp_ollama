import os
import asyncio
from typing import Optional
import time
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from pathlib import Path
import shutil
from llama_index.tools.mcp import BasicMCPClient, McpToolSpec
from llama_index.llms.ollama import Ollama
from llama_index.core import Settings
from llama_index.core.agent.workflow import (
    FunctionAgent,
    ToolCallResult,
    ToolCall,
                                             )
from llama_index.core.workflow import Context
from apscheduler.schedulers.background import BackgroundScheduler
from pdf2image import convert_from_path
import tempfile
import shutil
from pdf_helper import initialize_and_process 



OLLAMA_URL = os.environ.get("OLLAMA_URL")
MODEL = os.environ.get("OLLAMA_MODEL")
PDF_DIR = os.environ.get("PDF_DIR", "./res")
RES_DIR = os.environ.get("RES_DIR", "./res")

SYSTEM_PROMPT = """
Usa herramientas siempre.
Si la información ya está en el contexto de la conversación, puedes responder sin usar tools.
Podes usar unicamente una tool por cada consulta a menos que se te pida mas de una cosa.
Si no sabes la respuesta, responde con "No sé, y pedi mas informacion".
"""

scheduler = None

app = FastAPI()

_agent: Optional[FunctionAgent] = None
_agent_ctx: Optional[Context] = None

class MessageRequest(BaseModel):
    message: str

async def write_tools(tools): 
    for tool in tools:
        print(tool.metadata.name, tool.metadata.description)

"""
Crea el agente con las tools y el LLM, inlcuyendo el prompt del sistema.
"""        
def get_agent(tools, llm: Ollama):
    agent = FunctionAgent(
        name="Asistente",
        description="Un asistente que puede responder unsando tool",
        tools=tools,
        llm=llm,
        system_prompt=SYSTEM_PROMPT
    )
    return agent

"""
Define la comunicacion del modelo con el usuario, manejando el contexto como la utilizacion de las tools.
"""
async def handle_user_message(message_content: str, agent : FunctionAgent, agent_context : Context,verbose : bool = False) -> str:
    global chat_history
    handler = agent.run(message_content, ctx = agent_context)
    async for event in handler.stream_events():
        if verbose and type(event) == ToolCall:
            print(f" -- Llamando a la tool '{event.tool_name}' con los argumentos '{event.tool_kwargs}' --")
        elif verbose and type(event) == ToolCallResult:
            print(f"Tool {event.tool_name} respondio con {event}")

    response = await handler
    return str(response)

"""
Establce conexion con los MCPs y obtiene las tools, lo reintenta algunas veces si falla.
"""
async def gather_tools_from_urls(urls, retry_seconds=2, max_retries=30):
    mcp_tools = []
    for url in urls:
        #Inicializa el cliente MCP y crea el agente.
        client = BasicMCPClient(url)
        spec = McpToolSpec(client=client)

        retries = 0
        while True:
            try:
                tools = await spec.to_tool_list_async()
                print(f"[ok] Conectado a {url}, tools: {len(tools)}")
                mcp_tools.extend(tools)
                break
            except Exception as e:
                retries += 1
                print(f"[warn] No se pudo conectar a {url}: {e} (intento {retries})")
                if retries >= max_retries:
                    print(f"[error] Max retries alcanzado para {url}, lo omito.")
                    break
                await asyncio.sleep(retry_seconds)
    return mcp_tools

"""
Borra archivos PDF viejos en el directorio de uploads cada un dia.
"""
def delete_old_files():
    deleted_pdfs = 0
    deleted_dirs = 0

    try:
        for name in os.listdir(RES_DIR):
            path = os.path.join(RES_DIR, name)
            try:
                if os.path.isfile(path) and name.lower().endswith(".pdf") or name.lower().endswith(".png") or name.lower().endswith(".txt"):
                    os.remove(path)
                    deleted_pdfs += 1
                elif os.path.isdir(path):
                    shutil.rmtree(path)
                    deleted_dirs += 1
            except Exception as e:
                print(f"Error eliminando {path}: {e}")
    except Exception as e:
        print(f"Error listando RES_DIR ({RES_DIR}): {e}")
    print(f"PDFs eliminados: {deleted_pdfs}")
    print(f"Directorios eliminados: {deleted_dirs}")

@app.on_event("startup")
def iniciar_scheduler():
    global scheduler
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(delete_old_files, 'interval', days=1)
    scheduler.start()
    print("[info] Scheduler iniciado")

@app.on_event("shutdown")
def detener_scheduler():
    if scheduler:
        scheduler.shutdown()
        print("[info] Scheduler detenido")

@app.on_event("startup")
async def startup_event():
    global _agent, _agent_ctx

    #Setup llm Ollama
    llm = Ollama(model= MODEL,
                 base_url=OLLAMA_URL,
                 requests_timeout=300)
    Settings.llm = llm

    #Setup tools
    mcp_urls_env = os.environ.get("MCP_SERVERS")
    if not mcp_urls_env:
        print("[warn] No se encontró MCP_SERVERS en variables de entorno. No se cargarán tools.")
        mcp_urls = []
    else:
        mcp_urls = [u.strip() for u in mcp_urls_env.split(",") if u.strip()]
            
    mcp_tools = await gather_tools_from_urls(mcp_urls)
    if not mcp_tools:
        print("[error] No se obtuvieron tools desde ningun MCP. Revisar servidores.")
    else:
        await write_tools(mcp_tools)

    #Setup Agent
    _agent = get_agent(mcp_tools, llm)
    _agent_ctx = Context(_agent)
    print("[info] Agent inicializado. Endpoint /api/agent listo.")

"""
Endpoint para procesar mensajes de usuario y devolver respuestas del agente.
"""
@app.post("/api/agent")
async def api_agent(req: MessageRequest):

    global _agent, _agent_ctx
    if _agent is None or _agent_ctx is None:
        raise HTTPException(status_code=500, detail="Agent no inicializado aún o no hay tools cargadas.")

    user_input = req.message.strip()
    if not user_input:
        raise HTTPException(status_code=400, detail="El campo 'message' no puede estar vacío.")

    try:
        response = await handle_user_message(user_input, _agent, _agent_ctx ,verbose=True)
        return {"response": response}
    except Exception as e:
        print("[error] Al procesar la petición:", e)
        raise HTTPException(status_code=500, detail=str(e))
"""
Endpoint para procesar mensajes de usuario con archivo PDF adjunto y responder con preguntas referidas al contenido del PDF.
"""
@app.post("/api/agent/upload_pdf")
async def api_agent_upload(message: str = Form(...), file: UploadFile = File(...)):

    global _agent, _agent_ctx
    if _agent is None or _agent_ctx is None:
        raise HTTPException(status_code=500, detail="Agent no inicializado aún o no hay tools cargadas.")

    user_input = message.strip()
    if not user_input:
        raise HTTPException(status_code=400, detail="El campo 'message' no puede estar vacío.")

    if not file.filename:
        raise HTTPException(status_code=400, detail="No se ha subido ningún archivo.")
    
    if file.filename.split(".")[1] != "pdf":
        raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF. (por el momento)")

    file_path = os.path.join(RES_DIR, file.filename)

    #content = await file.read()
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    try:
        text = initialize_and_process(file_path)
        input_with_context = f"El siguiente es el texto extraído del PDF:\n\n{text}\n\nCon base en este texto, responde a la siguiente pregunta:\n{user_input}"

        response = await handle_user_message(input_with_context, _agent, _agent_ctx ,verbose=True)
        return {"response": response}

    except Exception as e:
        print("[error] Al procesar la petición:", e)
        raise HTTPException(status_code=500, detail=str(e))
