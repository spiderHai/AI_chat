"""数据模型定义"""
import operator
from typing import Annotated, List
from pydantic import BaseModel
from typing import TypedDict


class AgentState(TypedDict):
    """LangGraph Agent 的状态定义 - 数据在节点间流转的载体"""
    user_id: str
    question: str
    messages: Annotated[list, operator.add]  # 消息列表，自动累加
    thinking: str
    tool_to_use: str
    tool_result: str
    rag_context: str       # RAG 检索到的上下文
    final_response: str
    timestamp: str


class ChatRequest(BaseModel):
    """聊天请求"""
    question: str
    user_id: str = "default_user"
    use_rag: bool = True


class ChatResponse(BaseModel):
    """聊天响应"""
    answer: str
    thinking: str
    tools_used: List[str]
    rag_sources: List[str]
    timestamp: str


class DocumentUploadResponse(BaseModel):
    """文档上传响应"""
    success: bool
    chunks_added: int
    message: str
