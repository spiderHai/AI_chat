# LangGraph & LangChain 完整学习指南

## 📚 第一部分：LangChain 核心知识

### 1.1 LangChain 是什么？

LangChain 是一个 **LLM 应用框架**，帮助开发者快速构建 AI 应用。核心思想：

```
用户输入 → LangChain工具链 → LLM处理 → 应用输出
```

### 1.2 LangChain 五大核心模块

#### 📌 1. Model I/O（模型输入输出）
- **LLMs**: 与大模型交互（OpenAI、Claude、Qwen等）
- **Chat Models**: 对话模型（比单个LLM更适合聊天）
- **Prompts**: 提示词模板，支持动态变量
- **Output Parsers**: 解析模型输出

```python
# 示例：模型调用 + 提示词模板
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

prompt = ChatPromptTemplate.from_template(
    "用户问题：{question}\n请用中文回答。"
)
model = ChatOpenAI(model="gpt-4")
chain = prompt | model
result = chain.invoke({"question": "什么是AI？"})
```

#### 📌 2. Retrieval（检索）
用于 **RAG（检索增强生成）** - 让AI从自己的知识库回答

```python
# 向量数据库 + 检索
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings()
vectorstore = Chroma.from_texts(
    texts=["文本1", "文本2"],
    embedding=embeddings
)
relevant_docs = vectorstore.similarity_search("查询内容")
```

#### 📌 3. Chains（链）
将多个步骤串联起来

```python
# 简单链：提示词 | 模型 | 输出解析器
from langchain_core.output_parsers import StrOutputParser

chain = prompt | model | StrOutputParser()
```

#### 📌 4. Agents（智能体）
**关键概念**：让 AI 自己决定用什么工具、何时使用

```
Agent工作流程：
思考 → 选择工具 → 调用工具 → 观察结果 → 重复直到得出答案
```

#### 📌 5. Memory（记忆）
保存对话历史，让AI有上下文理解能力

```python
from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory()
memory.save_context(
    {"input": "你好"},
    {"output": "你好！很高兴认识你"}
)
```

---

## 🤖 第二部分：LangGraph - 多步骤Agent构建

### 2.1 为什么需要 LangGraph？

**问题场景：**
```
用户: "帮我查一下北京明天天气，然后推荐一个穿着方案"

所需步骤：
1. 解析用户问题 → 需要调用"天气查询"工具
2. 调用工具获取结果 → 得到天气数据
3. 基于天气数据 → 生成穿着推荐
```

**传统Agent的问题：**
- 难以控制决策流程
- 难以实现复杂的条件分支
- 难以追踪调试

**LangGraph的优势：**
- ✅ 显式定义状态机和流程图
- ✅ 支持条件分支、循环、并行执行
- ✅ 易于调试和可视化
- ✅ 完全可控的Agent流程

### 2.2 LangGraph 核心概念

#### 📊 图的三大要素

1. **Nodes（节点）** - 执行单位
   ```python
   def agent_node(state):
       """处理逻辑"""
       return {"response": "处理结果"}
   ```

2. **Edges（边）** - 节点之间的连接
   ```python
   graph.add_edge("node_a", "node_b")
   # 或条件边
   graph.add_conditional_edges("node_a", decide_next)
   ```

3. **State（状态）** - 流转数据
   ```python
   from typing import TypedDict

   class AgentState(TypedDict):
       question: str
       tool_calls: list
       result: str
   ```

### 2.3 LangGraph 工作流程图示

```
用户输入
    ↓
[开始节点] → 接收问题
    ↓
[思考节点] → LLM分析，决定是否需要工具
    ↓
  是否需要工具？
   /        \
  是         否
  ↓         ↓
[工具节点] [回答节点]
  ↓         ↓
[观察节点] [格式化]
  ↓         ↓
  └────→ [最终输出]
```

### 2.4 完整实现示例

```python
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from typing import TypedDict, Annotated
import operator

# 1️⃣ 定义状态
class AgentState(TypedDict):
    question: str
    messages: Annotated[list, operator.add]  # 累积消息
    tool_name: str
    tool_result: str

# 2️⃣ 定义节点
def thinking_node(state: AgentState):
    """思考阶段 - LLM分析问题"""
    model = ChatOpenAI(model="gpt-4")

    # 决定是否需要工具的提示词
    prompt = f"""
    用户问题: {state['question']}

    你需要决定是否需要调用工具。如果需要，说出工具名称。
    可用工具: weather, calculator, search

    格式: 需要工具[工具名] 或 不需要工具
    """

    response = model.invoke(prompt)
    return {
        "messages": [{"role": "assistant", "content": response.content}],
        "tool_name": extract_tool_name(response.content)
    }

def tool_node(state: AgentState):
    """工具调用阶段"""
    tool_name = state["tool_name"]

    # 根据工具名调用相应工具
    if tool_name == "weather":
        result = get_weather(state["question"])
    elif tool_name == "calculator":
        result = calculate(state["question"])
    else:
        result = "未知工具"

    return {
        "messages": [{"role": "user", "content": result}],
        "tool_result": result
    }

def answer_node(state: AgentState):
    """生成最终答案"""
    model = ChatOpenAI(model="gpt-4")

    context = f"""
    原问题: {state['question']}
    工具结果: {state['tool_result']}
    """

    response = model.invoke(context + "请基于以上信息回答问题")
    return {
        "messages": [{"role": "assistant", "content": response.content}]
    }

def should_use_tool(state: AgentState) -> str:
    """条件分支判断"""
    return "use_tool" if state["tool_name"] else "answer"

# 3️⃣ 构建图
graph = StateGraph(AgentState)

# 添加节点
graph.add_node("thinking", thinking_node)
graph.add_node("tool", tool_node)
graph.add_node("answer", answer_node)

# 添加边
graph.set_entry_point("thinking")  # 开始节点
graph.add_conditional_edges(
    "thinking",
    should_use_tool,
    {
        "use_tool": "tool",
        "answer": "answer"
    }
)
graph.add_edge("tool", "answer")  # 工具后一定要回答
graph.set_finish_point("answer")

# 4️⃣ 编译运行
runnable_graph = graph.compile()

result = runnable_graph.invoke({
    "question": "今天北京天气怎么样？",
    "messages": []
})

print(result["messages"][-1]["content"])
```

---

## 🛠️ 第三部分：实战对比

### 3.1 传统代码 vs LangChain vs LangGraph

#### 方案1：传统代码（硬编码逻辑）
```python
# ❌ 问题：逻辑死板，难以扩展
def handle_question(question):
    if "天气" in question:
        result = get_weather()
    elif "计算" in question:
        result = calculate()
    return format_answer(result)
```

#### 方案2：LangChain（自动化链）
```python
# ✓ 优点：简化调用，但流程不可控
from langchain.agents import initialize_agent, Tool

tools = [
    Tool(name="Weather", func=get_weather),
    Tool(name="Calculator", func=calculate),
]

agent = initialize_agent(tools, llm, agent_type="zero-shot-react-agent")
result = agent.run(question)
```

#### 方案3：LangGraph（完全可控）
```python
# ✅ 优点：图可视化，流程清晰，完全可控
# 见上面的完整示例
```

### 3.2 适用场景对比

| 场景 | 传统代码 | LangChain | LangGraph |
|------|--------|---------|----------|
| 简单聊天 | ✓ | ✓ | ✓ |
| 工具调用 | ✗ | ✓ | ✓ |
| 复杂多步骤 | ✗ | △ | ✓ |
| 需要人工干预 | ✗ | ✗ | ✓ |
| 生产级应用 | ✗ | ✓ | ✓ |

---

## 💡 第四部分：核心设计模式

### 4.1 提示词工程（Prompt Engineering）

```python
# 模式1：链式思考（Chain of Thought）
COT_PROMPT = """
解决问题的步骤：
1. 理解问题
2. 分解为子问题
3. 逐个解决
4. 总结答案

问题: {question}
"""

# 模式2：角色扮演（Role Playing）
ROLE_PROMPT = """
你是一位经验丰富的{role}。
背景: {background}
要求: {requirement}

用户问题: {question}
"""

# 模式3：少量示例（Few-Shot）
FEWSHOT_PROMPT = """
以下是解决问题的例子：
例子1: {example1_input} → {example1_output}
例子2: {example2_input} → {example2_output}

现在请解决: {question}
"""
```

### 4.2 输出解析（Output Parsing）

```python
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel

class QueryResult(BaseModel):
    answer: str
    confidence: float
    sources: list[str]

parser = PydanticOutputParser(pydantic_object=QueryResult)

prompt = ChatPromptTemplate.from_template("""
{format_instructions}

问题: {question}
""")

prompt = prompt.partial(format_instructions=parser.get_format_instructions())
chain = prompt | model | parser

result = chain.invoke({"question": "什么是AI？"})
print(result.answer)
print(result.confidence)
```

### 4.3 Agent的ReAct模式

```
思考 (Think) → 行动 (Act) → 观察 (Observe) → 反复循环
```

```python
# LangGraph实现ReAct
class ReActAgent:
    def __init__(self):
        self.thought_history = []
        self.action_history = []
        self.observation_history = []

    def think(self, state):
        """思考应该做什么"""
        thought = llm.invoke(f"当前状态: {state}\n请思考下一步")
        self.thought_history.append(thought)
        return {"thought": thought}

    def act(self, state):
        """执行行动"""
        thought = state["thought"]
        action = llm.invoke(f"基于思考: {thought}\n请选择行动")
        self.action_history.append(action)
        return {"action": action}

    def observe(self, state):
        """观察行动结果"""
        action = state["action"]
        observation = execute_action(action)
        self.observation_history.append(observation)
        return {"observation": observation}
```

---

## 📊 第五部分：高级特性

### 5.1 记忆管理（Memory）

```python
from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory

# 类型1：缓冲记忆 - 保存所有消息
memory = ConversationBufferMemory()

# 类型2：摘要记忆 - 定期总结
summary_memory = ConversationSummaryMemory(llm=model)

# 在Agent中使用
agent = initialize_agent(
    tools,
    llm,
    memory=memory,
    agent_type="conversational-react-description"
)
```

### 5.2 流式输出（Streaming）

```python
# 实时返回结果，改善用户体验
async def stream_response(question):
    async for chunk in chain.astream_events(
        {"question": question},
        version="v1"
    ):
        if chunk["event"] == "on_llm_stream":
            yield chunk["data"]["chunk"].content

# 在FastAPI中使用
from fastapi.responses import StreamingResponse

@app.post("/stream-chat")
async def stream_chat(request: QueryRequest):
    return StreamingResponse(
        stream_response(request.question),
        media_type="text/event-stream"
    )
```

### 5.3 并行执行（Parallel Execution）

```python
# 同时调用多个工具
from langchain.tools.parallel import ParallelToolExecutor

async def parallel_agent(question):
    # 同时执行多个工具
    tasks = [
        tool1.ainvoke(question),
        tool2.ainvoke(question),
        tool3.ainvoke(question),
    ]
    results = await asyncio.gather(*tasks)
    return combine_results(results)
```

---

## 🎯 第六部分：完整项目架构

### 推荐架构

```
AI_Chat/
├── backend/
│   ├── config.py          # 配置管理
│   ├── models.py          # 数据模型
│   ├── langgraph_agent.py # LangGraph Agent定义
│   ├── tools.py           # 工具函数集
│   ├── memory.py          # 记忆管理
│   └── main.py            # FastAPI应用
├── frontend/
│   ├── app.tsx            # 主应用
│   ├── hooks/
│   │   └── useChat.ts     # 聊天Hook
│   └── components/
│       └── ChatInterface.tsx
└── docker-compose.yml
```

### Agent定义示例（langgraph_agent.py）

```python
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from typing import Annotated
import operator

class AgentState(TypedDict):
    question: str
    messages: Annotated[list, operator.add]
    response: str

def agent_workflow():
    graph = StateGraph(AgentState)

    # 添加节点...

    return graph.compile()

agent = agent_workflow()
```

---

## 📚 学习路径建议

1. **第1周**：掌握 LangChain 基础（Model I/O、Prompts）
2. **第2周**：学习 Chains 和 Agents
3. **第3周**：深入 LangGraph 和复杂工作流
4. **第4周**：集成到项目，构建完整应用

## 🔗 相关资源

- [LangChain官方文档](https://python.langchain.com/)
- [LangGraph文档](https://langchain-ai.github.io/langgraph/)
- [LangSmith调试平台](https://www.langchain.com/langsmith)
