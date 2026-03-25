# 提示词管理 & 大模型 API 封装 — 学习指南

## 一、为什么需要这两个东西？

你现在的 RAG Agent 已经能跑了，但原来的写法有两个问题：

```python
# 旧写法：提示词和业务逻辑混在一起，难维护
def answer_node(state):
    context = f"""用户问题: {state['question']}
    相关文档内容: {state.get('rag_context', '无')}
    请基于以上文档内容回答..."""

    # 旧写法：裸调 API，没有重试、没有错误处理
    resp = requests.post(API_URL, json=payload, timeout=30)
```

拆分后：
- **prompts.py** — 所有提示词集中管理，改提示词不用翻业务代码
- **llm.py** — API 调用封装，自动重试、错误处理、多模型切换

---

## 二、提示词管理核心知识（prompts.py）

### 2.1 大模型的三种角色 (Role)

大模型 API 接收的消息列表中，每条消息都有一个 `role`：

| role | 含义 | 类比 |
|------|------|------|
| `system` | 系统指令，定义 AI 的行为 | 老板给员工的工作手册 |
| `user` | 用户说的话 | 客户的提问 |
| `assistant` | AI 之前的回复 | 员工之前的回答记录 |

```python
messages = [
    {"role": "system", "content": "你是知识库助手，只基于文档回答"},  # ← 行为约束
    {"role": "user", "content": "基础版多少钱？"},                   # ← 示例问题
    {"role": "assistant", "content": "基础版 ¥99/月"},              # ← 示例回答
    {"role": "user", "content": "价格方案"},                        # ← 真正的问题
]
```

### 2.2 System Prompt 设计原则

好的 System Prompt 包含四要素：

```
角色定义：你是一个专业的知识库助手
能力边界：你只能基于提供的文档内容回答
输出格式：用中文回答，语气友好专业
行为约束：不要编造文档中不存在的内容
```

对应代码 → `prompts.py` 中的 `SYSTEM_PROMPTS` 字典

### 2.3 Prompt Template（提示词模板）

把固定的骨架和动态的内容分开：

```python
# prompts.py
RAG_ANSWER_TEMPLATE = PromptTemplate(
    template="用户问题: {question}\n文档内容:\n{context}\n请回答。",
    required_vars=["question", "context"]
)

# 使用时
prompt = RAG_ANSWER_TEMPLATE.render(
    question="价格方案",
    context="基础版：¥99/月..."
)
```

### 2.4 Few-Shot Prompting（少样本提示）

给 AI 看几个示例，它就学会了输出格式：

```python
messages = [
    {"role": "system", "content": "你是知识库助手"},
    # ↓ 示例1（教 AI 怎么回答）
    {"role": "user", "content": "基础版多少钱？"},
    {"role": "assistant", "content": "根据文档，基础版 ¥99/月，包含..."},
    # ↓ 示例2
    {"role": "user", "content": "支持私有化吗？"},
    {"role": "assistant", "content": "是的，企业版支持私有化部署..."},
    # ↓ 真正的问题
    {"role": "user", "content": "价格方案"},
]
```

对应代码 → `prompts.py` 中的 `RAG_FEW_SHOT_EXAMPLES` + `PromptBuilder.set_few_shot()`

### 2.5 PromptBuilder 组合器

把所有片段拼装成完整的 messages：

```python
# agent.py 中的 answer_node
messages = (
    PromptBuilder()
    .set_system("rag_qa")                  # 1. 系统提示词
    .set_few_shot(RAG_FEW_SHOT_EXAMPLES)   # 2. 少样本示例
    .set_context(rag_context)              # 3. 检索到的文档
    .set_user_message("价格方案")           # 4. 用户问题
    .build_messages()                       # → 组装！
)
```

---

## 三、大模型 API 封装核心知识（llm.py）

### 3.1 关键参数

```
temperature (0~2)     控制随机性
├── 0     → 每次输出一样（适合：事实问答、数据提取）
├── 0.7   → 正常（适合：一般对话）
└── >1    → 很随机（适合：创意写作）

top_p (0~1)           另一种随机性控制
├── 0.1   → 只选最可能的词
└── 1.0   → 所有词都有机会

max_tokens            输出长度上限
├── 1中文字 ≈ 1~2 token
└── 设太小会截断，设太大浪费钱
```

### 3.2 错误处理与重试

```
API 可能返回的错误：
├── 429 (Rate Limit)  → 请求太频繁，等一会儿重试
├── 500 (Server Error) → 服务器故障，等一会儿重试
├── 400 (Bad Request)  → 参数错误，不重试（你的代码有bug）
└── Timeout           → 网络超时，重试

重试策略：指数退避
├── 第1次失败 → 等 1 秒
├── 第2次失败 → 等 2 秒
└── 第3次失败 → 等 4 秒 → 放弃
```

对应代码 → `llm.py` 中的 `LLMClient._call_api()`

### 3.3 Token 与计费

```
你发给 API 的内容 → input_tokens（输入 token）
API 返回的内容   → output_tokens（输出 token）

费用 = input_tokens × 输入单价 + output_tokens × 输出单价

省钱技巧：
1. System Prompt 尽量精简（每次请求都会发送）
2. Few-Shot 示例别太多（2-3个够了）
3. RAG 检索结果控制数量（k=3 而不是 k=10）
4. 简单任务用便宜模型（turbo），复杂任务才用贵的（plus）
```

对应代码 → `llm.py` 中的 `LLMClient._log_usage()`

### 3.4 流式输出 (Streaming)

```
普通模式：  用户等待 5秒... → 一次性显示完整回答
流式模式：  用户看到 "我" → "我们" → "我们提供" → ... （打字效果）
```

对应代码 → `llm.py` 中的 `LLMClient.chat_stream()`

### 3.5 多模型策略

```python
# 不同任务用不同模型，平衡效果和成本
analyze_node:  model=ModelType.TURBO,  temperature=0.3  # 分析：要快、要稳
answer_node:   model=ModelType.TURBO,  temperature=0.7  # 回答：可以有变化
# 如果效果不够好，answer_node 可以换成 PLUS
```

---

## 四、完整数据流（结合新代码）

```
用户: "价格方案"
  │
  ▼
[retrieve_node] ← rag_manager.search()
  │ 检索到文档: "基础版：¥99/月..."
  ▼
[analyze_node]
  │ ANALYZE_TEMPLATE.render(question, context)  ← 模板渲染
  │ → llm.chat(prompt, model=TURBO, temp=0.3)  ← 便宜模型
  │ 输出: "用户在询问产品定价信息"
  ▼
[answer_node]
  │ PromptBuilder()                              ← 组合器
  │   .set_system("rag_qa")                      ← 系统提示词
  │   .set_few_shot(examples)                    ← 少样本示例
  │   .set_context(rag_context)                  ← 检索结果
  │   .set_user_message("价格方案")               ← 用户问题
  │   .build_messages()                          ← 组装成 messages
  │ → llm.chat_with_messages(messages, TURBO)    ← 发给大模型
  ▼
"我们提供三种价格方案：基础版 ¥99/月..."
```

---

## 五、文件清单

| 文件 | 职责 | 核心知识点 |
|------|------|-----------|
| `prompts.py` | 提示词管理 | System Prompt、模板、Few-Shot、组合器 |
| `llm.py` | API 封装 | Messages格式、参数调优、重试、流式、多模型 |
| `agent.py` | Agent 图 | 如何把 prompts + llm 集成到 LangGraph |
