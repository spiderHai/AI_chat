"""Data models used by the app_skill04 service."""
import operator
from typing import Annotated, List, TypedDict

from pydantic import BaseModel


class AgentState(TypedDict):
    """State shared between LangGraph nodes."""

    user_id: str
    question: str
    messages: Annotated[list, operator.add]
    thinking: str
    tool_to_use: str
    tool_result: str
    rag_context: str
    final_response: str
    timestamp: str


class ChatRequest(BaseModel):
    """Chat request payload."""

    question: str
    user_id: str = "default_user"
    use_rag: bool = True


class ChatResponse(BaseModel):
    """Chat response payload."""

    answer: str
    thinking: str
    tools_used: List[str]
    rag_sources: List[str]
    timestamp: str


class DocumentUploadResponse(BaseModel):
    """Document upload response."""

    success: bool
    chunks_added: int
    message: str


class SkillRunRequest(BaseModel):
    """Request body for running a local demo skill."""

    skill_name: str
    question: str = ""
    context: str = ""


class MCPDemoRequest(BaseModel):
    """Request body for running the demo MCP flow."""

    question: str
    resource_uri: str = "project://architecture/rag_flow"
