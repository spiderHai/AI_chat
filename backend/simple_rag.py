"""
简化版 RAG - 聚焦检索核心
使用 Milvus Lite + DashScope Embedding
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import os
import requests
from dotenv import load_dotenv
from pymilvus import MilvusClient

load_dotenv()

# DashScope API 配置
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
DASHSCOPE_EMBEDDING_URL = "https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding"
DASHSCOPE_LLM_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"

# Milvus Lite 配置
MILVUS_DB_PATH = "./milvus_demo.db"
COLLECTION_NAME = "rag_docs"

# 初始化 Milvus Lite 客户端
milvus_client = MilvusClient(MILVUS_DB_PATH)


def get_embedding(text: str) -> List[float]:
    """获取文本向量"""
    headers = {
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "text-embedding-v1",
        "input": {"texts": [text]}
    }
    resp = requests.post(DASHSCOPE_EMBEDDING_URL, json=payload, headers=headers, timeout=30)
    result = resp.json()
    return result["output"]["embeddings"][0]["embedding"]


def call_llm(prompt: str) -> str:
    """调用 LLM"""
    headers = {
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "qwen-turbo",
        "input": {"messages": [{"role": "user", "content": prompt}]}
    }
    resp = requests.post(DASHSCOPE_LLM_URL, json=payload, headers=headers, timeout=30)
    return resp.json()["output"]["text"]


def init_collection():
    """初始化集合"""
    if milvus_client.has_collection(COLLECTION_NAME):
        milvus_client.drop_collection(COLLECTION_NAME)

    milvus_client.create_collection(
        collection_name=COLLECTION_NAME,
        dimension=1536,  # text-embedding-v1 的维度
        metric_type="COSINE"
    )


# 数据模型
class AddDocRequest(BaseModel):
    text: str
    title: str = "文档"


class QueryRequest(BaseModel):
    question: str
    top_k: int = 3


class QueryResponse(BaseModel):
    answer: str
    sources: List[dict]


# FastAPI 应用
app = FastAPI(title="简化版 RAG API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    """启动时初始化"""
    init_collection()
    print("✓ Milvus Lite 已初始化")


@app.post("/add")
async def add_document(req: AddDocRequest):
    """添加文档"""
    # 1. 获取向量
    vector = get_embedding(req.text)

    # 2. 插入 Milvus
    data = [{
        "id": milvus_client.num_entities(COLLECTION_NAME),
        "vector": vector,
        "text": req.text,
        "title": req.title
    }]
    milvus_client.insert(COLLECTION_NAME, data)

    return {"success": True, "message": f"已添加文档: {req.title}"}


@app.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    """RAG 查询"""
    # 1. 检索：将问题向量化
    query_vector = get_embedding(req.question)

    # 2. 检索：在 Milvus 中搜索相似文档
    results = milvus_client.search(
        collection_name=COLLECTION_NAME,
        data=[query_vector],
        limit=req.top_k,
        output_fields=["text", "title"]
    )

    # 3. 增强：构建上下文
    if not results[0]:
        return QueryResponse(answer="未找到相关文档", sources=[])

    context = "\n\n".join([f"[{hit['entity']['title']}]\n{hit['entity']['text']}" for hit in results[0]])

    # 4. 生成：基于上下文回答
    prompt = f"""基于以下文档回答问题。

文档内容:
{context}

问题: {req.question}

请基于文档内容回答，如果文档中没有相关信息，请说明。"""

    answer = call_llm(prompt)

    sources = [{"title": hit['entity']['title'], "score": hit['distance']} for hit in results[0]]

    return QueryResponse(answer=answer, sources=sources)


@app.get("/stats")
async def stats():
    """统计信息"""
    return {
        "total_docs": milvus_client.num_entities(COLLECTION_NAME),
        "collection": COLLECTION_NAME
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
