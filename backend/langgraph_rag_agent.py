"""
LangGraph RAG Agent - 检索增强生成
支持：文档加载、向量检索、智能问答
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import AsyncGenerator, Optional, Annotated, List
from datetime import datetime
import json
import asyncio
import operator
import os
import requests
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import pickle
from pathlib import Path

# LangChain & LangGraph 导入
from langgraph.graph import StateGraph, END
from langchain_core.tools import tool
from typing import TypedDict

# RAG 相关导入
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

load_dotenv()

# DashScope API 配置
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
DASHSCOPE_API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
DASHSCOPE_EMBEDDING_URL = "https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding"

# 向量数据库存储路径
VECTOR_STORE_PATH = "vector_store"
DOCUMENTS_PATH = "documents"

# 确保目录存在
os.makedirs(VECTOR_STORE_PATH, exist_ok=True)
os.makedirs(DOCUMENTS_PATH, exist_ok=True)


def call_qwen(prompt: str) -> str:
    """调用通义千问 qwen-turbo"""
    headers = {
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "qwen-turbo",
        "input": {
            "messages": [
                {"role": "user", "content": prompt}
            ]
        },
        "parameters": {}
    }
    resp = requests.post(DASHSCOPE_API_URL, json=payload, headers=headers, timeout=30)
    if resp.status_code != 200:
        return f"API调用失败: {resp.status_code} {resp.text}"
    result = resp.json()
    if "output" in result and "text" in result["output"]:
        return result["output"]["text"]
    return "无法获取AI回复"


def get_embeddings(texts: List[str]) -> List[List[float]]:
    """调用 DashScope Embedding API 获取文本向量"""
    headers = {
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "text-embedding-v1",
        "input": {
            "texts": texts
        }
    }
    resp = requests.post(DASHSCOPE_EMBEDDING_URL, json=payload, headers=headers, timeout=30)
    if resp.status_code != 200:
        raise Exception(f"Embedding API调用失败: {resp.status_code} {resp.text}")

    result = resp.json()
    if "output" in result and "embeddings" in result["output"]:
        return [item["embedding"] for item in result["output"]["embeddings"]]
    raise Exception("无法获取嵌入向量")


class DashScopeEmbeddings(Embeddings):
    """DashScope 嵌入模型包装器"""

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """嵌入多个文档"""
        # DashScope API 限制每次最多25个文本
        batch_size = 25
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            embeddings = get_embeddings(batch)
            all_embeddings.extend(embeddings)

        return all_embeddings

    def embed_query(self, text: str) -> List[float]:
        """嵌入单个查询"""
        return get_embeddings([text])[0]


# ==================== RAG 管理器 ====================

class RAGManager:
    """RAG 文档管理器"""
    def __init__(self):
        self.embeddings = DashScopeEmbeddings()
        self.vector_store = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,  # 每个文档块的大小
            chunk_overlap=50,  # 块之间的重叠
            length_function=len,
        )
        self._load_vector_store()

    def _load_vector_store(self):
        """加载已有的向量数据库"""
        index_path = os.path.join(VECTOR_STORE_PATH, "faiss_index")
        if os.path.exists(index_path):
            try:
                self.vector_store = FAISS.load_local(
                    VECTOR_STORE_PATH,
                    self.embeddings,
                    "faiss_index",
                    allow_dangerous_deserialization=True
                )
                print("✓ 向量数据库加载成功")
            except Exception as e:
                print(f"✗ 向量数据库加载失败: {e}")
                self.vector_store = None

    def add_documents_from_text(self, text: str, metadata: dict = None) -> int:
        """从文本添加文档"""
        # 分割文本
        texts = self.text_splitter.split_text(text)
        documents = [
            Document(page_content=t, metadata=metadata or {})
            for t in texts
        ]

        # 创建或更新向量数据库
        if self.vector_store is None:
            self.vector_store = FAISS.from_documents(documents, self.embeddings)
        else:
            self.vector_store.add_documents(documents)

        # 保存
        self.vector_store.save_local(VECTOR_STORE_PATH, "faiss_index")
        return len(documents)

    def add_documents_from_file(self, file_path: str) -> int:
        """从文件添加文档"""
        loader = TextLoader(file_path, encoding="utf-8")
        documents = loader.load()

        # 分割文档
        split_docs = self.text_splitter.split_documents(documents)

        # 添加到向量数据库
        if self.vector_store is None:
            self.vector_store = FAISS.from_documents(split_docs, self.embeddings)
        else:
            self.vector_store.add_documents(split_docs)

        # 保存
        self.vector_store.save_local(VECTOR_STORE_PATH, "faiss_index")
        return len(split_docs)

    def search(self, query: str, k: int = 3) -> List[Document]:
        """搜索相关文档"""
        if self.vector_store is None:
            return []

        results = self.vector_store.similarity_search(query, k=k)
        return results

    def get_stats(self) -> dict:
        """获取统计信息"""
        if self.vector_store is None:
            return {"total_documents": 0, "status": "empty"}

        return {
            "total_documents": self.vector_store.index.ntotal,
            "status": "ready"
        }


# ==================== 数据模型 ====================

class AgentState(TypedDict):
    """Agent状态定义"""
    user_id: str
    question: str
    messages: Annotated[list, operator.add]
    thinking: str
    tool_to_use: str
    tool_result: str
    rag_context: str  # RAG 检索的上下文
    final_response: str
    timestamp: str


class ChatRequest(BaseModel):
    """聊天请求"""
    question: str
    user_id: str = "default_user"
    use_rag: bool = True  # 是否使用 RAG


class ChatResponse(BaseModel):
    """聊天响应"""
    answer: str
    thinking: str
    tools_used: List[str]
    rag_sources: List[str]  # RAG 来源
    timestamp: str


class DocumentUploadResponse(BaseModel):
    """文档上传响应"""
    success: bool
    chunks_added: int
    message: str


# ==================== RAG Agent 实现 ====================

class RAGChatAgent:
    """带 RAG 功能的聊天 Agent"""

    def __init__(self, rag_manager: RAGManager):
        self.rag_manager = rag_manager
        self.agent_graph = self._build_graph()

    def _build_graph(self):
        """构建 Agent 工作流"""

        def retrieve_node(state: AgentState) -> dict:
            """检索相关文档"""
            question = state["question"]

            # 从向量数据库检索
            docs = self.rag_manager.search(question, k=3)

            if docs:
                context = "\n\n".join([
                    f"[文档 {i+1}]\n{doc.page_content}"
                    for i, doc in enumerate(docs)
                ])
                sources = [f"文档片段 {i+1}" for i in range(len(docs))]
            else:
                context = "未找到相关文档"
                sources = []

            return {
                "messages": [{"role": "system", "content": f"检索到 {len(docs)} 个相关文档"}],
                "rag_context": context,
                "tool_result": f"检索到 {len(docs)} 个文档片段"
            }

        def analyze_node(state: AgentState) -> dict:
            """分析问题"""
            prompt = f"""用户问题: {state['question']}

            检索到的相关信息:
            {state.get('rag_context', '无')}

            基于以上信息，分析问题并决定如何回答。
            以JSON格式响应:
            {{"thinking": "思考过程", "need_more_info": false}}
            """

            response_text = call_qwen(prompt)

            try:
                data = json.loads(response_text)
                thinking = data.get("thinking", response_text)
            except:
                thinking = response_text

            return {
                "messages": [{"role": "assistant", "content": thinking}],
                "thinking": thinking
            }

        def answer_node(state: AgentState) -> dict:
            """生成答案"""
            context = f"""用户问题: {state['question']}

相关文档内容:
{state.get('rag_context', '无相关文档')}

请基于以上文档内容回答用户问题。如果文档中没有相关信息，请诚实告知。
生成友好、专业、准确的回答。"""

            response_text = call_qwen(context)

            return {
                "messages": [{"role": "assistant", "content": response_text}],
                "final_response": response_text
            }

        # 构建图
        graph = StateGraph(AgentState)
        graph.add_node("retrieve", retrieve_node)
        graph.add_node("analyze", analyze_node)
        graph.add_node("answer", answer_node)

        graph.set_entry_point("retrieve")
        graph.add_edge("retrieve", "analyze")
        graph.add_edge("analyze", "answer")
        graph.set_finish_point("answer")

        return graph.compile()

    async def invoke(self, request: ChatRequest) -> ChatResponse:
        """异步调用 Agent"""

        initial_state = {
            "user_id": request.user_id,
            "question": request.question,
            "messages": [],
            "thinking": "",
            "tool_to_use": "",
            "tool_result": "",
            "rag_context": "",
            "final_response": "",
            "timestamp": datetime.now().isoformat()
        }

        # 在事件循环中运行同步的 Agent
        result = await asyncio.to_thread(
            self.agent_graph.invoke,
            initial_state
        )

        # 提取 RAG 来源
        rag_sources = []
        if result.get("rag_context") and result["rag_context"] != "未找到相关文档":
            rag_sources = ["文档片段 1", "文档片段 2", "文档片段 3"]

        return ChatResponse(
            answer=result["final_response"],
            thinking=result.get("thinking", ""),
            tools_used=["RAG检索"] if request.use_rag else [],
            rag_sources=rag_sources,
            timestamp=result["timestamp"]
        )


# ==================== FastAPI 应用 ====================

# 全局实例
rag_manager: Optional[RAGManager] = None
agent: Optional[RAGChatAgent] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global rag_manager, agent

    # 启动
    print("正在初始化 RAG 系统...")
    rag_manager = RAGManager()

    # 如果向量数据库为空，自动加载 documents 目录下的文件
    if rag_manager.vector_store is None:
        docs_dir = Path(DOCUMENTS_PATH)
        if docs_dir.exists():
            for file_path in docs_dir.glob("*.txt"):
                try:
                    count = rag_manager.add_documents_from_file(str(file_path))
                    print(f"✓ 已加载文档: {file_path.name} ({count} 个文档块)")
                except Exception as e:
                    print(f"✗ 加载文档失败 {file_path.name}: {e}")

    agent = RAGChatAgent(rag_manager)
    stats = rag_manager.get_stats()
    print(f"✓ RAG Agent 已初始化，向量库状态: {stats}")

    yield

    # 关闭
    print("✓ RAG Agent 已关闭")


app = FastAPI(
    title="AI聊天API - RAG版本",
    version="3.0.0",
    lifespan=lifespan
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 路由 ====================

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """RAG 聊天接口"""
    try:
        response = await agent.invoke(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """上传文档到 RAG 系统"""
    try:
        # 保存文件
        file_path = os.path.join(DOCUMENTS_PATH, file.filename)
        content = await file.read()

        with open(file_path, "wb") as f:
            f.write(content)

        # 添加到向量数据库
        chunks_added = rag_manager.add_documents_from_file(file_path)

        return DocumentUploadResponse(
            success=True,
            chunks_added=chunks_added,
            message=f"文档 {file.filename} 已成功添加，共 {chunks_added} 个文档块"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/documents/add-text", response_model=DocumentUploadResponse)
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


@app.get("/api/documents/stats")
async def get_stats():
    """获取文档统计信息"""
    return rag_manager.get_stats()


@app.get("/api/health")
async def health():
    """健康检查"""
    return {
        "status": "ok",
        "agent_ready": agent is not None,
        "rag_ready": rag_manager is not None,
        "vector_store_ready": rag_manager.vector_store is not None if rag_manager else False,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/info")
async def info():
    """获取API信息"""
    return {
        "name": "AI聊天API - RAG版本",
        "version": "3.0.0",
        "features": [
            "RAG 检索增强生成",
            "文档向量化",
            "智能问答",
            "文档管理",
            "语义搜索"
        ],
        "rag_stats": rag_manager.get_stats() if rag_manager else {}
    }


# ==================== 启动命令 ====================
"""
安装依赖:
pip install fastapi uvicorn langchain langchain-community faiss-cpu python-dotenv requests pydantic

启动服务:
uvicorn langgraph_rag_agent:app --reload --host 0.0.0.0 --port 8000

测试上传文档:
curl -X POST http://localhost:8000/api/documents/add-text \
-H "Content-Type: application/json" \
-d '{"text": "我们公司提供AI解决方案，包括智能客服、知识库管理等服务。", "title": "公司介绍"}'

测试聊天:
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "你们公司提供什么服务？", "user_id": "user001", "use_rag": true}'
"""
