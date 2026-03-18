# LangGraph & LangChain 完整实战指南

## 📦 第一部分：环境安装

### 1.1 Python依赖安装

```bash
# 基础依赖
pip install langgraph langchain langchain-openai langchain-community

# FastAPI后端
pip install fastapi uvicorn python-dotenv pydantic

# 可选的扩展
pip install langsmith          # 调试平台
pip install langchain-chroma   # 向量存储
pip install langchain-postgres # 数据库集成
```

### 1.2 前端依赖安装（React）

```bash
cd frontend

# 如果使用Next.js
npm install

# 如果是普通React
npm install react react-dom
```

### 1.3 验证安装

```bash
# Python验证
python -c "import langgraph; import langchain; print('✓ 安装成功')"

# Node.js验证
npm list react
```

---

## 🔑 第二部分：API密钥配置

### 2.1 获取OpenAI API密钥

1. 访问 https://platform.openai.com/account/api-keys
2. 创建新密钥
3. 保存密钥

### 2.2 获取其他LLM密钥

**阿里云通义千问（Qwen）：**
```bash
# 访问：https://dashscope.console.aliyun.com/api-key
# 创建API密钥
```

**Anthropic Claude：**
```bash
# 访问：https://console.anthropic.com/account/keys
# 获取API密钥
```

### 2.3 配置环境变量

**创建 `.env` 文件**
```bash
# OpenAI
OPENAI_API_KEY=sk-xxxxxxxxxxxx
OPENAI_MODEL=gpt-4

# Qwen（可选）
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxx

# Anthropic（可选）
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxx

# LangSmith调试（可选）
LANGSMITH_API_KEY=lsv2_xxxxxxxxxxxx
LANGSMITH_TRACING_V2=true
LANGSMITH_PROJECT=your-project-name
```

**在代码中加载**
```python
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
```

---

## 🚀 第三部分：快速开始

### 3.1 运行Agent示例

```bash
# 进入后端目录
cd backend

# 运行简单示例
python langgraph_agent_example.py

# 输出示例：
# ============================================================
# 开始处理用户问题: 怎么重置密码？
# ============================================================
# 🤔 [分析阶段] 用户问题: 怎么重置密码？
# 💭 思考: 用户询问密码重置，这是常见FAQ问题
# 🔧 决定使用: search_faq
# 🔨 [工具调用阶段] 执行工具: search_faq
# ✓ 工具结果: ✓ FAQ匹配: 请访问登录页面，点击'忘记密码'，按提示操作
# ...
```

### 3.2 启动FastAPI服务

```bash
# 方式1：使用uvicorn
uvicorn langgraph_fastapi_agent:app --reload --host 0.0.0.0 --port 8000

# 方式2：使用Python直接运行
python -m uvicorn langgraph_fastapi_agent:app --reload

# 访问API文档：http://localhost:8000/docs
```

### 3.3 调用API测试

**同步调用：**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "你们的产品是什么？",
    "user_id": "user001"
  }'
```

**健康检查：**
```bash
curl http://localhost:8000/api/health
```

**获取API信息：**
```bash
curl http://localhost:8000/api/info
```

### 3.4 WebSocket实时通信

```bash
# 使用websocat工具
websocat ws://localhost:8000/ws/chat

# 或使用在线工具：https://www.piesocket.com/websocket-tester

# 发送消息格式：
{"question": "你好", "user_id": "user001"}
```

---

## 💻 第四部分：前端集成

### 4.1 基础使用

```typescript
// pages/chat.tsx 或 app/chat.tsx
import { ChatInterface } from '@/hooks/useLangGraphChat';

export default function ChatPage() {
  return <ChatInterface />;
}
```

### 4.2 自定义Hook使用

```typescript
import { useChat } from '@/hooks/useLangGraphChat';

function MyChat() {
  const {
    messages,
    isLoading,
    thinking,
    toolsUsed,
    streamChat,
    clearMessages,
  } = useChat({
    apiUrl: 'http://localhost:8000',
    userId: 'my_user_123',
  });

  const handleSend = async (question) => {
    await streamChat(question);
  };

  return (
    <div>
      {messages.map((msg) => (
        <div key={msg.timestamp} className={msg.role}>
          {msg.content}
        </div>
      ))}

      {thinking && <p>💭 {thinking}</p>}
      {toolsUsed.length > 0 && <p>🔧 使用了: {toolsUsed.join(', ')}</p>}

      <input
        onKeyPress={(e) => {
          if (e.key === 'Enter') {
            handleSend(e.currentTarget.value);
            e.currentTarget.value = '';
          }
        }}
        disabled={isLoading}
        placeholder="输入问题..."
      />
    </div>
  );
}
```

### 4.3 流式输出配置

```typescript
const { streamChat } = useChat({
  apiUrl: 'http://localhost:8000',
  onStreamChunk: (chunk) => {
    // 每个字符都会触发此回调
    console.log('输出中:', chunk);
    // 可用于更新UI、播放音效等
  },
});
```

---

## 🛠️ 第五部分：自定义工具开发

### 5.1 创建自定义工具

```python
from langchain_core.tools import tool

@tool
def get_weather(location: str) -> str:
    """获取天气信息

    Args:
        location: 城市名称

    Returns:
        天气信息
    """
    # 实现逻辑
    weather_api = f"https://api.weather.com/city={location}"
    # 调用API或数据库
    return f"{location}: 晴天, 25°C"

# 使用工具
result = get_weather.invoke({"location": "北京"})
print(result)  # 北京: 晴天, 25°C
```

### 5.2 添加工具到Agent

```python
from langgraph.prebuilt import create_react_agent

tools = [
    search_faq,
    get_order_info,
    process_refund,
    get_weather,  # 新工具
]

agent = create_react_agent(model, tools)
```

### 5.3 复杂工具示例 - 数据库查询

```python
from langchain_core.tools import tool
from sqlalchemy import create_engine

@tool
def query_database(sql: str) -> str:
    """执行SQL查询

    Args:
        sql: SQL语句（自动验证安全性）

    Returns:
        查询结果
    """
    # 安全验证
    if any(kw in sql.upper() for kw in ['DROP', 'DELETE', 'TRUNCATE']):
        return "❌ 不允许执行删除操作"

    engine = create_engine("postgresql://user:password@localhost/db")
    with engine.connect() as conn:
        result = conn.execute(sql)
        return str(result.fetchall())
```

---

## 📊 第六部分：高级特性

### 6.1 对话记忆系统

```python
from langchain.memory import ConversationBufferMemory
from typing import List

class ChatWithMemory:
    def __init__(self):
        self.memory = ConversationBufferMemory()
        self.max_history = 20  # 最多保存20条消息

    def add_message(self, question: str, answer: str):
        """添加消息到记忆"""
        self.memory.save_context(
            {"input": question},
            {"output": answer}
        )

        # 超过限制则删除最早的
        if len(self.memory.buffer) > self.max_history:
            # 清理逻辑
            pass

    def get_context(self) -> str:
        """获取对话上下文"""
        return self.memory.buffer

# 使用
chat_memory = ChatWithMemory()
chat_memory.add_message("你好", "你好，很高兴认识你")
context = chat_memory.get_context()
```

### 6.2 异步并发执行

```python
import asyncio
from langchain_core.tools import tool

@tool
async def async_search_tool(query: str) -> str:
    """异步搜索工具"""
    await asyncio.sleep(1)  # 模拟网络请求
    return f"搜索结果: {query}"

async def run_parallel_tools(queries: List[str]):
    """并行执行多个工具"""
    tasks = [async_search_tool.ainvoke({"query": q}) for q in queries]
    results = await asyncio.gather(*tasks)
    return results
```

### 6.3 流式输出优化

```python
async def stream_chat_response(question: str):
    """生成流式响应"""

    agent = build_agent_graph()

    async for event in agent.astream_events(
        {"question": question},
        version="v1"
    ):
        if event["event"] == "on_llm_stream":
            # 实时返回流式数据
            yield event["data"]["chunk"].content
        elif event["event"] == "on_tool_start":
            # 工具开始执行
            yield f"\n🔧 使用工具: {event['name']}\n"
        elif event["event"] == "on_tool_end":
            # 工具完成
            yield f"✓ 工具完成\n"
```

---

## 🔍 第七部分：调试和监控

### 7.1 使用LangSmith调试

```python
import os
from langsmith import Client

# 配置LangSmith
os.environ["LANGSMITH_API_KEY"] = "your-key"
os.environ["LANGSMITH_TRACING_V2"] = "true"
os.environ["LANGSMITH_PROJECT"] = "my-project"

# 自动记录所有调用
# 访问 https://smith.langchain.com 查看
```

### 7.2 日志记录

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# 在Agent中使用
logger.debug(f"Agent输入: {state}")
logger.info(f"工具调用: {tool_name}")
logger.error(f"执行失败: {error}")
```

### 7.3 性能监控

```python
import time
from functools import wraps

def monitor_performance(func):
    """性能监控装饰器"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start
            print(f"✓ {func.__name__} 耗时: {duration:.2f}s")
            return result
        except Exception as e:
            duration = time.time() - start
            print(f"✗ {func.__name__} 失败，耗时: {duration:.2f}s")
            raise
    return wrapper

@monitor_performance
async def stream_chat(question: str):
    # ... 实现
    pass
```

---

## 📈 第八部分：生产部署

### 8.1 Docker容器化

**Dockerfile**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY backend ./backend
COPY .env .

CMD ["uvicorn", "backend.langgraph_fastapi_agent:app", "--host", "0.0.0.0", "--port", "8000"]
```

**requirements.txt**
```
langgraph==0.0.x
langchain==0.x.x
langchain-openai==0.x.x
fastapi==0.x.x
uvicorn==0.x.x
python-dotenv==0.x.x
```

### 8.2 Docker Compose编排

**docker-compose.yml**
```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - LANGSMITH_API_KEY=${LANGSMITH_API_KEY}
    volumes:
      - ./backend:/app/backend
    networks:
      - ai-chat

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    depends_on:
      - backend
    networks:
      - ai-chat

networks:
  ai-chat:
```

### 8.3 启动应用

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f backend

# 停止服务
docker-compose down
```

---

## ⚠️ 第九部分：常见问题

### Q1: Agent调用工具时出现错误怎么办？

**解决方案：**
```python
# 添加错误处理
try:
    result = agent.invoke(state)
except Exception as e:
    logger.error(f"Agent执行失败: {e}")
    # 降级到人工客服
    return escalate_to_human(str(e))
```

### Q2: 如何提升Agent响应速度？

**优化方案：**
1. 使用更快的模型（如GPT-3.5-turbo）
2. 减少工具数量
3. 使用缓存机制
4. 异步并发执行

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_search(query: str) -> str:
    """缓存搜索结果"""
    return search_faq(query)
```

### Q3: 如何处理超长对话历史？

```python
from langchain.memory import ConversationSummaryMemory

# 自动总结对话
memory = ConversationSummaryMemory(
    llm=model,
    max_token_limit=4000
)
```

### Q4: Token成本太高怎么办？

```python
# 1. 使用便宜的模型
model = ChatOpenAI(model="gpt-3.5-turbo")  # 比gpt-4便宜

# 2. 添加缓存
from langchain.cache import RedisCache

langchain.llm_cache = RedisCache(redis_=redis_client)

# 3. 批量处理
batch_results = await asyncio.gather(*[
    agent.ainvoke(state) for state in states
])
```

---

## 📚 学习资源

- **官方文档：** https://python.langchain.com/
- **LangGraph文档：** https://langchain-ai.github.io/langgraph/
- **API参考：** https://api.python.langchain.com/
- **社区论坛：** https://github.com/langchain-ai/langchain/discussions
- **示例代码：** https://github.com/langchain-ai/langchain/tree/master/examples

---

## 🎯 下一步建议

1. ✅ 理解LangChain核心概念（Model I/O、Chains、Agents）
2. ✅ 掌握LangGraph工作流（Nodes、Edges、State）
3. ✅ 开发和集成自定义工具
4. ✅ 优化Agent性能和成本
5. ✅ 部署到生产环境
6. ✅ 监控和维护

祝你开发愉快！🚀
