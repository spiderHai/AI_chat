"""
LangGraph Agent 完整实现示例
演示：智能客服Agent，支持FAQ、工具调用、对话记忆
"""

from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph
from langchain_core.tools import tool
import operator
import json
import os
import requests
from datetime import datetime
from dotenv import load_dotenv

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

# ==================== 1. 定义状态 ====================

class AgentState(TypedDict):
    """Agent工作状态"""
    question: str                           # 用户问题
    messages: Annotated[list, operator.add]  # 消息历史
    thinking: str                           # AI思考过程
    tool_to_use: str                        # 需要使用的工具
    tool_result: str                        # 工具执行结果
    final_response: str                     # 最终回复
    steps: list                             # 执行步骤记录


# ==================== 2. 定义工具 ====================

@tool
def search_faq(question: str) -> str:
    """搜索FAQ知识库"""
    faq_db = {
        "如何重置密码": "请访问登录页面，点击'忘记密码'，按提示操作",
        "订单怎么查询": "进入'我的订单'，输入订单号可查看详情",
        "如何退货": "在订单详情页点击'申请退货'，选择原因并提交",
        "咨询客服": "拨打400-1234-5678或访问在线客服",
    }

    # 简单的模糊匹配
    for key, value in faq_db.items():
        if key in question or any(word in question for word in key.split()):
            return f"✓ FAQ匹配: {value}"

    return "× 知识库未找到相关答案，需要转接人工客服"


@tool
def get_order_info(order_id: str) -> str:
    """查询订单信息"""
    # 模拟订单数据库
    orders = {
        "ORD001": {
            "status": "已发货",
            "items": "iPhone 15",
            "price": "¥5999",
            "date": "2024-03-15"
        },
        "ORD002": {
            "status": "待发货",
            "items": "MacBook Pro",
            "price": "¥12999",
            "date": "2024-03-17"
        }
    }

    if order_id in orders:
        info = orders[order_id]
        return json.dumps(info, ensure_ascii=False, indent=2)
    return f"未找到订单 {order_id}"


@tool
def process_refund(order_id: str, reason: str) -> str:
    """处理退款申请"""
    return f"✓ 已提交退款申请\n订单: {order_id}\n原因: {reason}\n预计24小时内处理"


@tool
def escalate_to_human(reason: str) -> str:
    """升级到人工客服"""
    return f"✓ 已申请转接人工客服，原因: {reason}\n客服将在5分钟内联系您"


# 工具集合
tools = [search_faq, get_order_info, process_refund, escalate_to_human]


# ==================== 3. 定义节点 ====================

def node_analyze_question(state: AgentState) -> dict:
    """分析问题节点 - 确定是否需要工具"""
    print(f"\n🤔 [分析阶段] 用户问题: {state['question']}")

    # 分析提示词
    analysis_prompt = f"""你是一个智能客服Agent。用户问题: {state['question']}

分析问题类型，从以下工具中选择最合适的：
1. search_faq - 搜索FAQ知识库（常见问题）
2. get_order_info - 查询订单信息（需要订单号）
3. process_refund - 处理退款申请
4. escalate_to_human - 转接人工客服（问题复杂）
5. none - 直接回答，无需工具

请以JSON格式响应：
{{
    "thinking": "你的分析过程",
    "tool": "工具名称或none",
    "reason": "选择理由"
}}
"""

    response_text = call_qwen(analysis_prompt)

    try:
        result = json.loads(response_text)
        tool_name = result.get("tool", "none")
        thinking = result.get("thinking", "")
    except:
        tool_name = "none"
        thinking = response_text

    print(f"💭 思考: {thinking}")
    print(f"🔧 决定使用: {tool_name}")

    return {
        "messages": [{"role": "assistant", "content": thinking}],
        "thinking": thinking,
        "tool_to_use": tool_name,
        "steps": [f"[分析] 决定使用工具: {tool_name}"]
    }


def node_use_tool(state: AgentState) -> dict:
    """工具调用节点"""
    tool_name = state["tool_to_use"]
    print(f"\n🔨 [工具调用阶段] 执行工具: {tool_name}")

    # 从问题中提取参数
    question = state["question"]

    if tool_name == "search_faq":
        result = search_faq.invoke({"question": question})

    elif tool_name == "get_order_info":
        # 从问题中提取订单号
        order_id = extract_order_id(question)
        result = get_order_info.invoke({"order_id": order_id})

    elif tool_name == "process_refund":
        order_id = extract_order_id(question)
        result = process_refund.invoke({"order_id": order_id, "reason": question})

    elif tool_name == "escalate_to_human":
        result = escalate_to_human.invoke({"reason": question})

    else:
        result = "未执行工具"

    print(f"✓ 工具结果: {result[:100]}...")

    return {
        "messages": [{"role": "user", "content": f"工具({tool_name})结果: {result}"}],
        "tool_result": result,
        "steps": [f"[工具] {tool_name}: {result[:50]}..."]
    }


def node_generate_response(state: AgentState) -> dict:
    """生成最终回复节点"""
    print(f"\n✍️  [回答阶段] 生成最终回复")

    # 构建上下文
    context = f"用户问题: {state['question']}\n"

    if state["tool_result"]:
        context += f"工具结果: {state['tool_result']}\n"

    context += f"""思考过程: {state['thinking']}

请基于上述信息，用友好、专业的语气回答用户的问题。
如果用户问题涉及多个方面，尽量全部解决。
"""

    final_response = call_qwen(context)

    print(f"📝 回复: {final_response[:100]}...")

    return {
        "messages": [{"role": "assistant", "content": final_response}],
        "final_response": final_response,
        "steps": [f"[回答] 已生成回复"]
    }


# ==================== 4. 条件分支 ====================

def should_use_tool(state: AgentState) -> Literal["use_tool", "direct_answer"]:
    """判断是否需要使用工具"""
    if state["tool_to_use"] != "none":
        return "use_tool"
    return "direct_answer"


# ==================== 5. 构建图 ====================

def build_agent_graph():
    """构建LangGraph Agent"""

    graph = StateGraph(AgentState)

    # 添加节点
    graph.add_node("analyze", node_analyze_question)
    graph.add_node("tool", node_use_tool)
    graph.add_node("answer", node_generate_response)

    # 设置入口点
    graph.set_entry_point("analyze")

    # 添加条件分支
    graph.add_conditional_edges(
        "analyze",
        should_use_tool,
        {
            "use_tool": "tool",
            "direct_answer": "answer"
        }
    )

    # 工具执行后必须生成回答
    graph.add_edge("tool", "answer")

    # 答案是终点
    graph.set_finish_point("answer")

    # 编译
    return graph.compile()


# ==================== 6. 工具函数 ====================

def extract_order_id(text: str) -> str:
    """从文本中提取订单号"""
    import re
    match = re.search(r'ORD\d+', text)
    return match.group() if match else "ORD001"


# ==================== 7. 运行Agent ====================

def run_agent(question: str) -> dict:
    """运行Agent并返回结果"""
    print("=" * 60)
    print(f"开始处理用户问题: {question}")
    print("=" * 60)

    agent = build_agent_graph()

    initial_state = {
        "question": question,
        "messages": [],
        "thinking": "",
        "tool_to_use": "",
        "tool_result": "",
        "final_response": "",
        "steps": []
    }

    result = agent.invoke(initial_state)

    print("\n" + "=" * 60)
    print("📊 执行步骤:")
    for step in result["steps"]:
        print(f"  {step}")
    print("\n✅ 最终回复:")
    print(result["final_response"])
    print("=" * 60)

    return result


# ==================== 8. 使用示例 ====================

if __name__ == "__main__":
    # 测试场景
    test_questions = [
        "怎么重置密码？",
        "我的订单ORD001发货了吗？",
        "我想退货，应该怎么做？",
        "如何联系客服？",
    ]

    for q in test_questions:
        result = run_agent(q)
        print("\n\n")
