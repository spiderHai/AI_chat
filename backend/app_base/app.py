"""FastAPI 应用入口 - 生命周期管理 + CORS"""
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import DOCUMENTS_PATH
from .rag_manager import RAGManager
from .agent import RAGChatAgent
from . import routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化 RAG 系统"""
    print("正在初始化 RAG 系统...")
    routes.rag_manager = RAGManager()

    # 如果向量数据库为空，自动加载 documents 目录下的文件
    if routes.rag_manager.vector_store is None:
        docs_dir = Path(DOCUMENTS_PATH)
        if docs_dir.exists():
            for file_path in docs_dir.glob("*.txt"):
                try:
                    count = routes.rag_manager.add_documents_from_file(str(file_path))
                    print(f"✓ 已加载文档: {file_path.name} ({count} 个文档块)")
                except Exception as e:
                    print(f"✗ 加载文档失败 {file_path.name}: {e}")

    routes.agent = RAGChatAgent(routes.rag_manager)
    stats = routes.rag_manager.get_stats()
    print(f"✓ RAG Agent 已初始化，向量库状态: {stats}")

    yield

    print("✓ RAG Agent 已关闭")


app = FastAPI(
    title="AI聊天API - RAG版本",
    version="3.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes.router)
