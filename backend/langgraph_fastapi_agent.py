"""
LangGraph Agent 集成FastAPI - 完整生产版本
支持：异步调用、流式输出、对话记忆、多用户
"""

from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import AsyncGenerator, Optional, Annotated
from datetime import datetime
import json
import asyncio
import operator
import os
import requests
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# LangChain & LangGraph 导入
from langgraph.graph import StateGraph, END
from langchain_core.tools import tool
from typing import TypedDict

load_dotenv()

# DashScope API 配置（与 main.py 一致）
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
DASHSCOPE_API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"


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

# ==================== 数据模型 ====================

class AgentState(TypedDict):
    """Agent状态定义"""
    user_id: str
    question: str
    messages: Annotated[list, operator.add]
    thinking: str
    tool_to_use: str
    tool_result: str
    final_response: str
    timestamp: str


class ChatMessage(BaseModel):
    """聊天消息"""
    role: str  # 'user' 或 'assistant'
    content: str
    timestamp: Optional[str] = None


class ChatRequest(BaseModel):
    """聊天请求"""
    question: str
    user_id: str = "default_user"
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    """聊天响应"""
    answer: str
    thinking: str
    tools_used: list[str]
    timestamp: str


# ==================== 工具定义 ====================

@tool
def search_knowledge_base(query: str) -> str:
    """搜索知识库

    Args:
        query: 搜索关键词

    Returns:
        搜索结果
    """
    knowledge_base = {
        "产品": "我们提供AI聊天解决方案、智能客服系统、知识库管理等",
        "价格": "基础版¥99/月，专业版¥299/月，企业版定制价格",
        "支持": "提供邮件、电话、在线客服24/7支持",
        "部署": "支持云部署、私有化部署、混合部署",
    }

    for key, value in knowledge_base.items():
        if key in query:
            return f"✓ 知识库答案: {value}"

    return "✗ 知识库未找到相关内容，建议查询其他资源或联系人工客服"


@tool
def get_user_info(user_id: str) -> str:
    """获取用户信息

    Args:
        user_id: 用户ID

    Returns:
        用户信息JSON
    """
    # 模拟用户数据库
    users = {
        "user001": {
            "name": "张三",
            "subscription": "专业版",
            "status": "活跃",
            "last_login": "2024-03-17 14:30"
        },
        "default_user": {
            "name": "游客",
            "subscription": "免费版",
            "status": "试用",
            "last_login": datetime.now().isoformat()
        }
    }

    if user_id in users:
        return json.dumps(users[user_id], ensure_ascii=False, indent=2)
    return json.dumps(users["default_user"], ensure_ascii=False)


@tool
def log_interaction(user_id: str, question: str, answer: str) -> str:
    """记录交互历史

    Args:
        user_id: 用户ID
        question: 用户问题
        answer: 系统回答

    Returns:
        确认消息
    """
    # 实际项目中应该保存到数据库
    return f"✓ 已记录 | 用户:{user_id} | 问题:{question[:30]}... | 时间:{datetime.now()}"


@tool
def escalate_to_human(reason: str, priority: str = "normal") -> str:
    """升级到人工客服

    Args:
        reason: 升级原因
        priority: 优先级 (normal/high/urgent)

    Returns:
        升级确认
    """
    return f"✓ 已提交人工升级 | 原因:{reason} | 优先级:{priority} | 预计响应时间:5分钟"


# 工具集合
tools = [
    search_knowledge_base,
    get_user_info,
    log_interaction,
    escalate_to_human
]


# ==================== Agent实现 ====================

class LangGraphChatAgent:
    """LangGraph聊天Agent"""

    def __init__(self):
        self.conversation_history = {}  # 用户对话历史
        self.agent_graph = self._build_graph()

    def _build_graph(self):
        """构建Agent工作流"""

        def analyze_node(state: AgentState) -> dict:
            """分析问题"""
            prompt = f"""用户问题: {state['question']}
用户ID: {state['user_id']}

分析问题，决定是否需要调用工具。
可用工具:
- search_knowledge_base: 搜索知识库
- get_user_info: 获取用户信息
- log_interaction: 记录交互
- escalate_to_human: 升级人工

以JSON格式响应:
{{"tool": "工具名或none", "thinking": "思考过程"}}
"""

            response_text = call_qwen(prompt)

            try:
                data = json.loads(response_text)
                tool_name = data.get("tool", "none")
                thinking = data.get("thinking", "")
            except:
                tool_name = "none"
                thinking = response_text

            return {
                "messages": [{"role": "assistant", "content": thinking}],
                "thinking": thinking,
                "tool_to_use": tool_name
            }

        def tool_node(state: AgentState) -> dict:
            """执行工具"""
            tool_name = state["tool_to_use"]

            if tool_name == "search_knowledge_base":
                result = search_knowledge_base.invoke({"query": state["question"]})
            elif tool_name == "get_user_info":
                result = get_user_info.invoke({"user_id": state["user_id"]})
            elif tool_name == "escalate_to_human":
                result = escalate_to_human.invoke({"reason": state["question"]})
            else:
                result = "未执行工具"

            return {
                "messages": [{"role": "user", "content": result}],
                "tool_result": result
            }

        def answer_node(state: AgentState) -> dict:
            """生成答案"""
            context = f"用户问题: {state['question']}\n用户ID: {state['user_id']}\n"

            if state.get("tool_result"):
                context += f"工具结果: {state['tool_result']}\n"

            context += "请生成友好、专业的回答。"

            response_text = call_qwen(context)

            return {
                "messages": [{"role": "assistant", "content": response_text}],
                "final_response": response_text
            }

        # 构建图
        graph = StateGraph(AgentState)
        graph.add_node("analyze", analyze_node)
        graph.add_node("tool", tool_node)
        graph.add_node("answer", answer_node)

        graph.set_entry_point("analyze")

        def route_decision(state: AgentState) -> str:
            return "tool" if state["tool_to_use"] != "none" else "answer"

        graph.add_conditional_edges(
            "analyze",
            route_decision,
            {"tool": "tool", "answer": "answer"}
        )

        graph.add_edge("tool", "answer")
        graph.set_finish_point("answer")

        return graph.compile()

    async def invoke(self, request: ChatRequest) -> ChatResponse:
        """异步调用Agent"""

        initial_state = {
            "user_id": request.user_id,
            "question": request.question,
            "messages": [],
            "thinking": "",
            "tool_to_use": "",
            "tool_result": "",
            "final_response": "",
            "timestamp": datetime.now().isoformat()
        }

        # 在事件循环中运行同步的Agent
        result = await asyncio.to_thread(
            self.agent_graph.invoke,
            initial_state
        )

        return ChatResponse(
            answer=result["final_response"],
            thinking=result["thinking"],
            tools_used=[result["tool_to_use"]] if result["tool_to_use"] != "none" else [],
            timestamp=result["timestamp"]
        )

    async def stream_invoke(self, request: ChatRequest) -> AsyncGenerator[str, None]:
        """流式调用Agent"""

        # 首先获取分析结果
        response = await self.invoke(request)

        # 逐字符流式输出
        for char in response.answer:
            yield char
            await asyncio.sleep(0.01)  # 模拟流式输出延迟


# ==================== FastAPI应用 ====================

# 全局Agent实例
agent: Optional[LangGraphChatAgent] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global agent
    # 启动
    agent = LangGraphChatAgent()
    print("✓ Agent已初始化")

    yield

    # 关闭
    print("✓ Agent已关闭")


app = FastAPI(
    title="AI聊天API - LangGraph版本",
    version="2.0.0",
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
    """同步聊天接口"""
    try:
        response = await agent.invoke(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health():
    """健康检查"""
    return {
        "status": "ok",
        "agent_ready": agent is not None,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/info")
async def info():
    """获取API信息"""
    return {
        "name": "AI聊天API - LangGraph版本",
        "version": "2.0.0",
        "features": [
            "智能问题分析",
            "工具调用",
            "对话记忆",
            "人工升级",
            "交互记录"
        ],
        "tools": [
            "search_knowledge_base",
            "get_user_info",
            "log_interaction",
            "escalate_to_human"
        ]
    }


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket聊天接口 - 实时通信"""
    await websocket.accept()

    try:
        while True:
            # 接收消息
            data = await websocket.receive_json()
            request = ChatRequest(**data)

            # 流式返回
            async for chunk in agent.stream_invoke(request):
                await websocket.send_text(chunk)

            # 发送结束标记
            await websocket.send_json({"type": "end"})

    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
    finally:
        await websocket.close()


# ==================== 启动命令 ====================
"""
安装依赖:
pip install langchain langgraph langchain-openai fastapi uvicorn

启动服务:
uvicorn main:app --reload --host 0.0.0.0 --port 8000

测试API:
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "你们的产品是什么？", "user_id": "user001"}'

WebSocket测试 (使用websocat或在线工具):
websocat ws://localhost:8000/ws/chat
"""
