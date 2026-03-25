"""配置常量"""
import os
from dotenv import load_dotenv

load_dotenv()

# DashScope API 配置
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
DASHSCOPE_API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
DASHSCOPE_EMBEDDING_URL = "https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding"

# 存储路径
VECTOR_STORE_PATH = "vector_store"
DOCUMENTS_PATH = "documents"

# 确保目录存在
os.makedirs(VECTOR_STORE_PATH, exist_ok=True)
os.makedirs(DOCUMENTS_PATH, exist_ok=True)
