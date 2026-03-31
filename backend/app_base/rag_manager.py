"""RAG 文档管理器 - 文档加载、分割、向量化、检索"""
import os
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document
from .config import VECTOR_STORE_PATH
from .embeddings import DashScopeEmbeddings
from .logger import get_logger, Timer

logger = get_logger("rag_manager")


class RAGManager:
    """RAG 文档管理器

    职责：管理文档的完整生命周期
    1. 加载文档（从文件或文本）
    2. 分割成小块
    3. 调用 Embedding API 向量化
    4. 存入 FAISS 向量数据库
    5. 根据查询做相似度检索
    """

    def __init__(self):
        self.embeddings = DashScopeEmbeddings()
        self.vector_store = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
        )
        self._load_vector_store()

    def _load_vector_store(self):
        """启动时尝试加载已有的 FAISS 索引"""
        index_path = os.path.join(VECTOR_STORE_PATH, "faiss_index")
        if os.path.exists(index_path):
            try:
                self.vector_store = FAISS.load_local(
                    VECTOR_STORE_PATH,
                    self.embeddings,
                    "faiss_index",
                    allow_dangerous_deserialization=True
                )
                logger.info("向量数据库加载成功")
            except Exception as e:
                logger.error("向量数据库加载失败", error=str(e))
                self.vector_store = None

    def add_documents_from_text(self, text: str, metadata: dict = None) -> int:
        """从文本添加文档到向量库"""
        texts = self.text_splitter.split_text(text)
        documents = [
            Document(page_content=t, metadata=metadata or {})
            for t in texts
        ]

        if self.vector_store is None:
            self.vector_store = FAISS.from_documents(documents, self.embeddings)
        else:
            self.vector_store.add_documents(documents)

        self.vector_store.save_local(VECTOR_STORE_PATH, "faiss_index")
        return len(documents)

    def add_documents_from_file(self, file_path: str) -> int:
        """从文件添加文档到向量库"""
        loader = TextLoader(file_path, encoding="utf-8")
        documents = loader.load()
        split_docs = self.text_splitter.split_documents(documents)

        if self.vector_store is None:
            self.vector_store = FAISS.from_documents(split_docs, self.embeddings)
        else:
            self.vector_store.add_documents(split_docs)

        self.vector_store.save_local(VECTOR_STORE_PATH, "faiss_index")
        return len(split_docs)

    def search(self, query: str, k: int = 3) -> List[Document]:
        """根据查询做相似度检索，返回最相关的 k 个文档块"""
        if self.vector_store is None:
            logger.warning("检索跳过: 向量库为空")
            return []
        timer = Timer()
        results = self.vector_store.similarity_search(query, k=k)
        logger.info("检索完成", results_count=len(results), duration_ms=timer.elapsed_ms())
        return results

    def get_stats(self) -> dict:
        """获取向量库统计信息"""
        if self.vector_store is None:
            return {"total_documents": 0, "status": "empty"}
        return {
            "total_documents": self.vector_store.index.ntotal,
            "status": "ready"
        }
