"""LangGraph RAG Agent - 核心工作流图"""
import json
import asyncio
from datetime import datetime
from langgraph.graph import StateGraph
from .llm import call_qwen
from .rag_manager import RAGManager
from .schemas import AgentState, ChatRequest, ChatResponse


class RAGChatAgent:
    """带 RAG 功能的聊天 Agent

    内部构建了一个 LangGraph 状态图，包含 3 个节点：
    retrieve（检索）→ analyze（分析）→ answer（回答）
    """

    def __init__(self, rag_manager: RAGManager):
        self.rag_manager = rag_manager
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
            """节点2: 让 LLM 分析问题和检索结果"""
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
            except Exception:
                thinking = response_text

            return {
                "messages": [{"role": "assistant", "content": thinking}],
                "thinking": thinking
            }

        def answer_node(state: AgentState) -> dict:
            """节点3: 基于检索上下文生成最终回答"""
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
