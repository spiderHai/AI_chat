"""FastAPI 应用入口 - 生命周期管理 + CORS + 中间件"""
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import DOCUMENTS_PATH
from .rag_manager import RAGManager
from .agent import RAGChatAgent
from .logger import get_logger
from .middleware import RequestTraceMiddleware
from . import routes

logger = get_logger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化 RAG 系统"""
    logger.info("正在初始化 RAG 系统...")
    routes.rag_manager = RAGManager()

    # 如果向量数据库为空，自动加载 documents 目录下的文件
    if routes.rag_manager.vector_store is None:
        docs_dir = Path(DOCUMENTS_PATH)
        if docs_dir.exists():
            for file_path in docs_dir.glob("*.txt"):
                try:
                    count = routes.rag_manager.add_documents_from_file(str(file_path))
                    logger.info("文档加载成功", file=file_path.name, chunks=count)
                except Exception as e:
                    logger.error("文档加载失败", file=file_path.name, error=str(e))

    routes.agent = RAGChatAgent(routes.rag_manager)
    stats = routes.rag_manager.get_stats()
    logger.info("RAG Agent 初始化完成", **stats)

    yield

    logger.info("RAG Agent 已关闭")


app = FastAPI(
    title="AI聊天API - RAG版本",
    version="3.0.0",
    lifespan=lifespan
)

# 中间件注册顺序很重要！
# 注册顺序和执行顺序是相反的（后注册的先执行）：
#   注册: CORS → RequestTrace
#   执行: RequestTrace（先）→ CORS → 路由处理 → CORS → RequestTrace（后）
# 所以 RequestTrace 要在 CORS 之后注册，才能最先拦截请求
app.add_middleware(RequestTraceMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes.router)
