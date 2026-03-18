"""
数据模型定义
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class QueryRequest(BaseModel):
    """聊天查询请求"""
    question: str = Field(..., min_length=1, max_length=2000, description="用户问题")


class ChatMessage(BaseModel):
    """聊天消息"""
    role: str = Field(..., description="消息角色: user 或 assistant")
    content: str = Field(..., description="消息内容")
    timestamp: Optional[str] = Field(None, description="消息时间戳")


class ChatResponse(BaseModel):
    """聊天响应"""
    answer: str = Field(..., description="AI 回答")
    timestamp: str = Field(..., description="响应时间戳")


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(..., description="服务状态")
    timestamp: str = Field(..., description="检查时间戳")
