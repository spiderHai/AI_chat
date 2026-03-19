"""FastAPI 路由定义"""
import os
import json
from datetime import datetime
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from .schemas import ChatRequest, ChatResponse, DocumentUploadResponse
from .config import DOCUMENTS_PATH

router = APIRouter()

# 这两个全局引用会在 app.py 的 lifespan 中被设置
rag_manager = None
agent = None


@router.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """RAG 聊天接口"""
    try:
        response = await agent.invoke(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """SSE 流式聊天接口"""
    async def event_generator():
        try:
            async for chunk in agent.invoke_stream(request):
                # SSE 格式: data: {...}\n\n
                data = json.dumps({"chunk": chunk}, ensure_ascii=False)
                yield f"data: {data}\n\n"
            # 发送结束标记
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


@router.post("/api/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """上传文档到 RAG 系统"""
    try:
        file_path = os.path.join(DOCUMENTS_PATH, file.filename)
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        chunks_added = rag_manager.add_documents_from_file(file_path)
        return DocumentUploadResponse(
            success=True,
            chunks_added=chunks_added,
            message=f"文档 {file.filename} 已成功添加，共 {chunks_added} 个文档块"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/documents/add-text", response_model=DocumentUploadResponse)
async def add_text(text: str, title: str = "未命名文档"):
    """直接添加文本到 RAG 系统"""
    try:
        chunks_added = rag_manager.add_documents_from_text(
            text,
            metadata={"title": title, "timestamp": datetime.now().isoformat()}
        )
        return DocumentUploadResponse(
            success=True,
            chunks_added=chunks_added,
            message=f"文本已成功添加，共 {chunks_added} 个文档块"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/documents/stats")
async def get_stats():
    return rag_manager.get_stats()


@router.get("/api/health")
async def health():
    return {
        "status": "ok",
        "agent_ready": agent is not None,
        "rag_ready": rag_manager is not None,
        "vector_store_ready": rag_manager.vector_store is not None if rag_manager else False,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/api/info")
async def info():
    return {
        "name": "AI聊天API - RAG版本",
        "version": "3.0.0",
        "features": ["RAG 检索增强生成", "文档向量化", "智能问答", "文档管理", "语义搜索"],
        "rag_stats": rag_manager.get_stats() if rag_manager else {}
    }
