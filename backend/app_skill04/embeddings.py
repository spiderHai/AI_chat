"""文本向量化层 - DashScope Embedding"""
import requests
from typing import List
from langchain_core.embeddings import Embeddings
from .config import DASHSCOPE_API_KEY, DASHSCOPE_EMBEDDING_URL


def get_embeddings(texts: List[str]) -> List[List[float]]:
    """调用 DashScope Embedding API 获取文本向量"""
    headers = {
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "text-embedding-v1",
        "input": {"texts": texts}
    }
    resp = requests.post(DASHSCOPE_EMBEDDING_URL, json=payload, headers=headers, timeout=30)
    if resp.status_code != 200:
        raise Exception(f"Embedding API调用失败: {resp.status_code} {resp.text}")

    result = resp.json()
    if "output" in result and "embeddings" in result["output"]:
        return [item["embedding"] for item in result["output"]["embeddings"]]
    raise Exception("无法获取嵌入向量")


class DashScopeEmbeddings(Embeddings):
    """DashScope 嵌入模型包装器，实现 LangChain Embeddings 接口"""

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """嵌入多个文档（自动分批，每批最多25条）"""
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
