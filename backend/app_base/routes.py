"""FastAPI route definitions for app_skill04."""
import json
import os
from datetime import datetime

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from .config import DOCUMENTS_PATH
from .logger import get_logger
from .mcp_demo import demo_mcp_client, demo_mcp_server
from .schemas import (
    ChatRequest,
    ChatResponse,
    DocumentUploadResponse,
    MCPDemoRequest,
    SkillRunRequest,
)
from .skills import skill_registry

logger = get_logger("routes")

router = APIRouter()

# These references are initialized in app.py lifespan.
rag_manager = None
agent = None


@router.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main RAG chat endpoint."""
    try:
        response = await agent.invoke(request)
        return response
    except Exception as exc:
        logger.error("Chat request failed", error=str(exc), exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """SSE streaming chat endpoint."""

    async def event_generator():
        try:
            async for chunk in agent.invoke_stream(request):
                data = json.dumps({"chunk": chunk}, ensure_ascii=False)
                yield f"data: {data}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as exc:
            logger.error("Streaming chat failed", error=str(exc), exc_info=True)
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/api/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload a text document into the RAG system."""
    try:
        file_path = os.path.join(DOCUMENTS_PATH, file.filename)
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        chunks_added = rag_manager.add_documents_from_file(file_path)
        logger.info("Document uploaded", filename=file.filename, chunks=chunks_added)
        return DocumentUploadResponse(
            success=True,
            chunks_added=chunks_added,
            message=f"Document {file.filename} loaded successfully. Added {chunks_added} chunks.",
        )
    except Exception as exc:
        logger.error("Document upload failed", filename=file.filename, error=str(exc), exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/api/documents/add-text", response_model=DocumentUploadResponse)
async def add_text(text: str, title: str = "untitled_document"):
    """Add raw text directly into the RAG system."""
    try:
        chunks_added = rag_manager.add_documents_from_text(
            text,
            metadata={"title": title, "timestamp": datetime.now().isoformat()},
        )
        logger.info("Text added", title=title, chunks=chunks_added)
        return DocumentUploadResponse(
            success=True,
            chunks_added=chunks_added,
            message=f"Text added successfully. Added {chunks_added} chunks.",
        )
    except Exception as exc:
        logger.error("Add text failed", title=title, error=str(exc), exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/api/documents/stats")
async def get_stats():
    return rag_manager.get_stats()


@router.get("/api/learn/overview")
async def learn_overview():
    """Beginner-friendly roadmap that ties skills and MCP to the current app."""
    return {
        "project": "app_skill04",
        "why_this_folder": (
            "This folder already contains route handling, prompts, LLM calls, and an agent graph, "
            "so it is a good place to learn how higher-level abstractions fit together."
        ),
        "two_step_plan": [
            "Step 1: learn skills as local reusable capabilities inside one app.",
            "Step 2: learn MCP as a standard way to expose resources and tools across apps or agents.",
        ],
        "current_code_mapping": {
            "route_layer": "backend/app_skill04/routes.py",
            "agent_layer": "backend/app_skill04/agent.py",
            "prompt_layer": "backend/app_skill04/prompts.py",
            "llm_layer": "backend/app_skill04/llm.py",
            "skill_demo": "backend/app_skill04/skills.py",
            "mcp_demo": "backend/app_skill04/mcp_demo.py",
        },
    }


@router.get("/api/learn/skills")
async def learn_skills():
    """List the local demo skills."""
    return {
        "concept": "A skill is a packaged capability with a clear purpose, input, and output.",
        "why_it_matters": (
            "Skills help you avoid putting every behavior directly into one giant prompt or one giant route."
        ),
        "skills": skill_registry.list_skills(),
    }


@router.post("/api/learn/skills/run")
async def run_skill(request: SkillRunRequest):
    """Run one local teaching skill."""
    result = skill_registry.run(
        skill_name=request.skill_name,
        question=request.question,
        context=request.context,
    )
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result)
    return result


@router.get("/api/learn/mcp")
async def learn_mcp():
    """Expose the tiny MCP-style demo server surface."""
    return {
        "concept": (
            "MCP separates the model runtime from external context/tools by using standard operations "
            "such as list resources, read resource, list tools, and call tool."
        ),
        "mental_model": [
            "Skill packages capability.",
            "MCP standardizes how capabilities and context are exposed.",
            "A local app can use both at the same time.",
        ],
        "resources": demo_mcp_server.list_resources(),
        "tools": demo_mcp_server.list_tools(),
    }


@router.post("/api/learn/mcp/demo")
async def run_mcp_demo(request: MCPDemoRequest):
    """Run a simulated MCP client flow."""
    result = demo_mcp_client.demo_learning_flow(
        question=request.question,
        resource_uri=request.resource_uri,
    )
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result)
    return result


@router.get("/api/health")
async def health():
    return {
        "status": "ok",
        "agent_ready": agent is not None,
        "rag_ready": rag_manager is not None,
        "vector_store_ready": rag_manager.vector_store is not None if rag_manager else False,
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/api/info")
async def info():
    return {
        "name": "AI Chat API - RAG + Skill + MCP demo",
        "version": "4.0.0",
        "features": [
            "RAG retrieval",
            "document ingestion",
            "streaming chat",
            "local skill demo",
            "MCP-style resource/tool demo",
        ],
        "rag_stats": rag_manager.get_stats() if rag_manager else {},
    }
