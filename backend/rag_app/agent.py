"""
LangGraph RAG Agent - 核心工作流图

展示如何把 提示词管理(prompts) + LLM封装(llm) + RAG检索(rag_manager)
三者组合起来，构建一个完整的 Agent 工作流。
"""
import asyncio
from datetime import datetime
from typing import AsyncGenerator
from langgraph.graph import StateGraph
from .llm import get_llm_client, ModelType
from .prompts import (
    PromptBuilder, ANALYZE_TEMPLATE,
    RAG_FEW_SHOT_EXAMPLES,
)
from .rag_manager import RAGManager
from .schemas import AgentState, ChatRequest, ChatResponse


class RAGChatAgent:
    """带 RAG 功能的聊天 Agent

    工作流: retrieve（检索）→ analyze（分析）→ answer（回答）

    相比旧版的改进：
    - 使用 PromptBuilder 组合提示词，而不是手拼字符串
    - 使用 LLMClient 调用模型，有重试和错误处理
    - 不同节点可以用不同模型（分析用 turbo，回答用 plus）
    """

    def __init__(self, rag_manager: RAGManager):
        self.rag_manager = rag_manager
        self.llm = get_llm_client()
        self.agent_graph = self._build_graph()

    def _build_graph(self):
        """构建 LangGraph 工作流图"""

        def retrieve_node(state: AgentState) -> dict:
            """节点1: 从向量库检索相关文档"""
            question = state["question"]
            docs = self.rag_manager.search(question, k=3)

            if docs:
                context = "\n\n".join([
                    f"[文档 {i+1}]\n{doc.page_content}"
                    for i, doc in enumerate(docs)
                ])
            else:
                context = "未找到相关文档"

            return {
                "messages": [{"role": "system", "content": f"检索到 {len(docs)} 个相关文档"}],
                "rag_context": context,
                "tool_result": f"检索到 {len(docs)} 个文档片段"
            }

        def analyze_node(state: AgentState) -> dict:
            """节点2: 用 PromptBuilder 构建分析提示词，让 LLM 分析问题

            这里展示了 PromptBuilder 的实际用法：
            旧写法: prompt = f"用户问题: {question}\\n检索到的信息: {context}..."
            新写法: 用 PromptBuilder 组合 system prompt + 模板，更清晰可维护
            """
            # 用模板渲染分析提示词
            prompt = ANALYZE_TEMPLATE.render(
                question=state["question"],
                context=state.get("rag_context", "无")
            )

            # 分析任务用 turbo 就够了（便宜、快）
            response_text = self.llm.chat(
                prompt,
                model=ModelType.TURBO,
                temperature=0.3  # 分析任务要稳定输出，temperature 调低
            )

            thinking = response_text
            try:
                import json
                data = json.loads(response_text)
                thinking = data.get("thinking", response_text)
            except Exception:
                pass

            return {
                "messages": [{"role": "assistant", "content": thinking}],
                "thinking": thinking
            }

        def answer_node(state: AgentState) -> dict:
            """节点3: 用 PromptBuilder 构建完整提示词，生成最终回答

            这里展示了 PromptBuilder 的完整能力：
            System Prompt + Few-Shot 示例 + RAG 上下文 + 用户问题
            全部组合成一个 messages 列表发给大模型。
            """
            # 用 PromptBuilder 组合所有提示词片段
            messages = (
                PromptBuilder()
                .set_system("rag_qa")                       # 1. 系统提示词
                .set_few_shot(RAG_FEW_SHOT_EXAMPLES)        # 2. 少样本示例
                .set_context(state.get("rag_context", ""))  # 3. RAG 检索上下文
                .set_user_message(state["question"])         # 4. 用户问题
                .build_messages()                            # → 组装成 messages 列表
            )

            # 回答任务用 messages 格式调用，效果更好
            response_text = self.llm.chat_with_messages(
                messages,
                model=ModelType.TURBO,
                temperature=0.7  # 回答可以稍微有点变化
            )

            return {
                "messages": [{"role": "assistant", "content": response_text}],
                "final_response": response_text
            }

        # 构建图: retrieve → analyze → answer
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
        """异步调用 Agent 图"""
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

        result = await asyncio.to_thread(
            self.agent_graph.invoke,
            initial_state
        )

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

    async def invoke_stream(self, request: ChatRequest) -> AsyncGenerator[str, None]:
        """流式调用：先检索，再流式生成回答"""
        # 1. 检索相关文档（同步，很快）
        docs = self.rag_manager.search(request.question, k=3)
        if docs:
            context = "\n\n".join([
                f"[文档 {i+1}]\n{doc.page_content}"
                for i, doc in enumerate(docs)
            ])
        else:
            context = "未找到相关文档"

        # 2. 构建提示词
        messages = (
            PromptBuilder()
            .set_system("rag_qa")
            .set_few_shot(RAG_FEW_SHOT_EXAMPLES)
            .set_context(context)
            .set_user_message(request.question)
            .build_messages()
        )

        # 3. 流式调用 LLM，逐块 yield
        for chunk in self.llm.chat_stream_with_messages(messages, model=ModelType.TURBO):
            yield chunk
