# LangChain vs LangGraph vs 传统代码 - 深度对比

## 📊 功能对比表

| 功能 | 传统代码 | LangChain | LangGraph |
|------|--------|---------|----------|
| **简单聊天** | ✓ | ✓✓ | ✓✓ |
| **模型调用** | △ | ✓✓ | ✓✓ |
| **工具集成** | ✗ | ✓✓ | ✓✓✓ |
| **智能体** | ✗ | ✓ | ✓✓✓ |
| **流程控制** | ✗ | △ | ✓✓✓ |
| **可视化** | ✗ | ✗ | ✓✓✓ |
| **调试** | △ | ✓ | ✓✓✓ |
| **内存管理** | ✗ | ✓✓ | ✓✓ |
| **扩展性** | ✗ | ✓✓ | ✓✓✓ |
| **学习曲线** | 容易 | 中等 | 中等 |

## 🔄 工作流程对比

### 传统代码流程
```
用户问题
    ↓
if/else 判断
    ↓
    ├─→ 分支1 → 调用API1 → 处理结果1
    ├─→ 分支2 → 调用API2 → 处理结果2
    └─→ 分支3 → 调用API3 → 处理结果3
    ↓
格式化输出
    ↓
返回结果

问题：
- 流程硬编码，难以修改
- 难以扩展新功能
- 重复代码多
- 难以追踪调试
```

### LangChain流程
```
用户问题
    ↓
Prompt Template (格式化提示词)
    ↓
LLM (调用模型)
    ↓
Agent (自动选择工具)
    ↓
    ├─→ 工具1
    ├─→ 工具2
    └─→ 工具3
    ↓
Output Parser (解析输出)
    ↓
返回结果

优点：
- 自动化工具选择
- 内置链式操作
- 易于扩展
- 支持流式输出

缺点：
- 流程不完全可控
- 调试困难
```

### LangGraph流程
```
开始
  ↓
[Input Node]
入队：状态初始化
  ↓
[Router]
    ↙        ↘
  需要工具    无需工具
    ↓          ↓
[Tool Node] [Answer Node]
  ↓            ↓
[Observer]     ↓
  ↓            ↓
  └──→ [Final Node] ←──┘
       返回结果

优点：
- 完全可控的流程
- 清晰的状态机
- 易于调试和可视化
- 支持复杂的分支和循环
```

## 💡 代码示例对比

### 场景：构建一个支持天气查询的聊天机器人

#### 方案1：传统代码（硬编码）
```python
def handle_question(question: str) -> str:
    """处理用户问题"""

    # 硬编码的判断逻辑
    if "天气" in question:
        # 提取城市
        city = extract_city(question)
        weather = get_weather_api(city)
        return f"{city}的天气是{weather}"

    elif "查询" in question and "订单" in question:
        order_id = extract_order_id(question)
        order = get_order(order_id)
        return f"订单状态：{order['status']}"

    elif "价格" in question:
        return "我们的产品价格如下..."

    else:
        return "抱歉，我不理解你的问题"

# 问题：
# - 每增加新功能都要修改if/else
# - 逻辑与数据混合
# - 难以测试
# - 难以维护
```

#### 方案2：LangChain（自动Agent）
```python
from langchain.agents import initialize_agent, Tool
from langchain_openai import ChatOpenAI

# 定义工具
tools = [
    Tool(
        name="Weather",
        func=lambda city: f"{city}的天气：晴天，25°C",
        description="查询城市天气"
    ),
    Tool(
        name="Order",
        func=lambda order_id: f"订单{order_id}已发货",
        description="查询订单状态"
    ),
]

# 创建Agent（自动选择工具）
llm = ChatOpenAI(model="gpt-4")
agent = initialize_agent(
    tools,
    llm,
    agent_type="zero-shot-react-agent",
    verbose=True
)

# 使用
result = agent.run("北京的天气怎么样？")

# 优点：
# - 自动判断需要什么工具
# - 易于扩展新工具
# - LLM智能理解问题

# 缺点：
# - 流程不可控
# - Agent可能做出意外选择
# - 难以调试
```

#### 方案3：LangGraph（完全可控）
```python
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from typing import TypedDict, Annotated, Literal
import operator

class State(TypedDict):
    question: str
    messages: Annotated[list, operator.add]
    tool_name: str
    result: str

def analyze_node(state: State) -> dict:
    """分析问题"""
    llm = ChatOpenAI(model="gpt-4")

    response = llm.invoke(f"""
    问题: {state['question']}

    判断需要什么工具？
    - weather: 天气查询
    - order: 订单查询
    - none: 无需工具

    回复: weather/order/none
    """)

    tool_name = response.content.strip()
    return {"tool_name": tool_name, "messages": []}

def weather_node(state: State) -> dict:
    """天气工具"""
    result = f"天气信息：晴天，25°C"
    return {"result": result, "messages": []}

def order_node(state: State) -> dict:
    """订单工具"""
    result = f"订单状态：已发货"
    return {"result": result, "messages": []}

def answer_node(state: State) -> dict:
    """生成答案"""
    llm = ChatOpenAI(model="gpt-4")

    context = f"问题: {state['question']}\n工具结果: {state.get('result', '')}"
    response = llm.invoke(context)

    return {"messages": [response.content]}

def route_tools(state: State) -> Literal["weather", "order", "answer"]:
    """路由判断"""
    if state["tool_name"] == "weather":
        return "weather"
    elif state["tool_name"] == "order":
        return "order"
    else:
        return "answer"

# 构建图
graph = StateGraph(State)
graph.add_node("analyze", analyze_node)
graph.add_node("weather", weather_node)
graph.add_node("order", order_node)
graph.add_node("answer", answer_node)

graph.set_entry_point("analyze")
graph.add_conditional_edges("analyze", route_tools, {
    "weather": "weather",
    "order": "order",
    "answer": "answer"
})
graph.add_edge("weather", "answer")
graph.add_edge("order", "answer")
graph.set_finish_point("answer")

runnable = graph.compile()

# 使用
result = runnable.invoke({"question": "北京的天气怎么样？", "messages": []})

# 优点：
# - 完全可控的流程
# - 清晰的逻辑
# - 易于调试
# - 可视化工作流
# - 支持复杂分支

# 比较：
# - 传统代码：最简单，但难以扩展
# - LangChain：自动化，但不可控
# - LangGraph：最灵活，需要多写代码
```

## 🎯 选择建议

### 使用传统代码的场景
```python
# 1. 简单的条件判断
if user_role == "admin":
    return get_admin_data()

# 2. 固定的工作流
validate → process → format

# 3. 实时性要求高，不需要AI分析
```

### 使用LangChain的场景
```python
# 1. 快速原型开发
# 2. 需要多种工具的自动选择
# 3. 不需要复杂的流程控制
# 4. 愿意牺牲部分控制权换取便利

agent = initialize_agent(tools, llm, agent_type="...")
```

### 使用LangGraph的场景
```python
# 1. 生产级应用
# 2. 需要完整的流程控制
# 3. 需要人工干预点
# 4. 需要复杂的分支和循环
# 5. 需要可视化调试

graph = StateGraph(State)
# 精细化构建工作流
```

## 📈 性能对比

### 响应时间
```
传统代码:        100ms
LangChain:       500-2000ms (取决于工具数)
LangGraph:       500-2000ms (取决于流程)

注：主要时间消耗在LLM调用上
```

### Token消耗
```
传统代码:        少量 (只有判断逻辑)
LangChain:       中等 (每次工具选择都需要LLM推理)
LangGraph:       可控 (根据流程设计)

优化建议：
1. 使用缓存减少重复调用
2. 使用更便宜的模型（gpt-3.5-turbo）
3. 批量处理请求
```

### 可扩展性
```
传统代码:        ✗ (O(n)复杂度增长)
LangChain:       ✓ (工具数量增加不影响复杂度)
LangGraph:       ✓✓ (完全可扩展)
```

## 🔌 集成复杂度

### 集成现有系统

**传统代码：**
```python
# 直接调用
result = legacy_function()
```

**LangChain：**
```python
from langchain_core.tools import tool

@tool
def legacy_tool(input_data: str) -> str:
    return legacy_function(input_data)

agent.tools.append(legacy_tool)
```

**LangGraph：**
```python
def legacy_node(state):
    result = legacy_function(state["input"])
    return {"result": result}

graph.add_node("legacy", legacy_node)
```

## 🚀 推荐方案

### 快速原型
```
推荐：传统代码 + LangChain
时间：1-2天
复杂度：低
```

### MVP产品
```
推荐：LangChain
时间：3-5天
复杂度：中
特点：快速上线，功能够用
```

### 生产应用
```
推荐：LangGraph
时间：7-14天
复杂度：中-高
特点：完全可控，可靠稳定
```

## 📚 学习路径

```
Day 1-2: 学习LangChain基础 (Model I/O, Chains)
Day 3-4: 学习Agents和工具
Day 5-6: 学习LangGraph工作流
Day 7-10: 构建完整项目
Day 11+: 优化、部署、监控
```
