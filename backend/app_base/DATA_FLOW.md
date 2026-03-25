# RAG Agent 数据流转说明

## 整体架构图

```
用户提问 "价格方案"
       │
       ▼
┌─────────────────┐
│  FastAPI 路由层   │  routes.py → POST /api/chat
│  接收 HTTP 请求   │
└───────┬─────────┘
        │ ChatRequest(question="价格方案")
        ▼
┌─────────────────┐
│  LangGraph Agent │  agent.py → RAGChatAgent.invoke()
│  状态图引擎       │
└───────┬─────────┘
        │ AgentState 在 3 个节点间流转
        ▼
┌──────────────────────────────────────────┐
│          LangGraph 状态图                  │
│                                           │
│  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │ retrieve  │→│ analyze  │→│ answer  │ │
│  │ 向量检索   │  │ LLM分析  │  │ LLM回答 │ │
│  └────┬─────┘  └────┬─────┘  └────┬────┘ │
│       │              │              │      │
└───────┼──────────────┼──────────────┼──────┘
        │              │              │
        ▼              ▼              ▼
   rag_manager.py   llm.py        llm.py
   (FAISS检索)     (call_qwen)   (call_qwen)
        │              │              │
        ▼              ▼              ▼
   embeddings.py   DashScope      DashScope
   (文本→向量)     Chat API       Chat API
```

## 两条核心数据流

---

### 流程一：文档入库（启动时自动执行）

当服务启动时，`app.py` 的 `lifespan()` 函数会自动把 `documents/` 目录下的 txt 文件加载到向量库。

```
sample_docs.txt
      │
      │ ① TextLoader 读取文件
      ▼
"AI Chat 产品介绍\n我们公司提供..."  （完整文本）
      │
      │ ② RecursiveCharacterTextSplitter 分割
      │   chunk_size=500, overlap=50
      ▼
["AI Chat 产品介绍\n我们公司...",    （文档块1，≤500字）
 "价格方案\n基础版：¥99/月...",      （文档块2）
 "技术特点\n我们的系统基于..."]       （文档块3）
      │
      │ ③ DashScopeEmbeddings.embed_documents()
      │   调用阿里云 Embedding API
      ▼
[[0.12, -0.34, 0.56, ...],           （1536维向量）
 [0.78, 0.23, -0.45, ...],
 [0.33, -0.67, 0.89, ...]]
      │
      │ ④ FAISS.from_documents() 建立索引
      ▼
vector_store/faiss_index              （磁盘持久化）
```

对应代码调用链：
```
app.py: lifespan()
  → rag_manager.py: RAGManager.add_documents_from_file()
    → TextLoader(file_path).load()           # 读文件
    → text_splitter.split_documents(docs)     # 切块
    → FAISS.from_documents(split_docs, self.embeddings)
      → embeddings.py: DashScopeEmbeddings.embed_documents()
        → embeddings.py: get_embeddings(texts)  # 调API
    → vector_store.save_local()               # 存磁盘
```

---

### 流程二：用户问答（每次聊天请求）

```
POST /api/chat  {"question": "价格方案"}
      │
      │ ① routes.py 接收请求
      ▼
agent.invoke(ChatRequest)
      │
      │ ② 构造初始 AgentState
      ▼
┌─────────────────────────────────────┐
│ AgentState = {                      │
│   question: "价格方案",              │
│   messages: [],                     │
│   rag_context: "",                  │
│   thinking: "",                     │
│   final_response: "",               │
│   ...                               │
│ }                                   │
└──────────────┬──────────────────────┘
               │
               ▼

**节点1: retrieve（向量检索）** → `agent.py: retrieve_node()`

```
"价格方案"
    │
    │ rag_manager.search("价格方案", k=3)
    │   → DashScopeEmbeddings.embed_query("价格方案")
    │     → 调用阿里云 Embedding API，得到查询向量
    │   → FAISS.similarity_search()
    │     → 用查询向量在索引中找最相似的3个文档块
    ▼
检索结果: [
  Document("价格方案\n基础版：¥99/月..."),   ← 最相关
  Document("AI Chat 产品介绍\n我们公司..."),
  Document("技术特点\n我们的系统基于...")
]
    │
    │ 拼接成 rag_context 字符串
    ▼
AgentState.rag_context = "[文档1]\n价格方案\n基础版..."
```

**节点2: analyze（LLM 分析）** → `agent.py: analyze_node()`

```
构造 prompt = "用户问题: 价格方案\n检索到的相关信息: [文档1]..."
    │
    │ llm.py: call_qwen(prompt)
    │   → POST 阿里云通义千问 API
    ▼
LLM 返回: {"thinking": "用户在询问产品定价..."}
    │
    ▼
AgentState.thinking = "用户在询问产品定价..."
```

**节点3: answer（生成回答）** → `agent.py: answer_node()`

```
构造 prompt = "用户问题: 价格方案\n相关文档内容: [文档1]价格方案..."
    │
    │ llm.py: call_qwen(prompt)
    │   → POST 阿里云通义千问 API
    │   → LLM 基于文档内容生成回答
    ▼
AgentState.final_response = "我们提供三种价格方案：
  基础版 ¥99/月，专业版 ¥299/月，企业版定制价格..."
```

**返回响应：**
```
AgentState → ChatResponse(
    answer="我们提供三种价格方案...",
    thinking="用户在询问产品定价...",
    tools_used=["RAG检索"],
    rag_sources=["文档片段 1", "文档片段 2", "文档片段 3"]
)
    │
    ▼
HTTP 200 JSON 响应 → 前端展示
```

---

## 模块依赖关系

```
app.py（入口）
  ├── config.py（配置）
  ├── routes.py（路由）
  │     ├── schemas.py（数据模型）
  │     └── agent.py（Agent 图）
  │           ├── llm.py（LLM 调用）
  │           ├── rag_manager.py（向量检索）
  │           │     ├── embeddings.py（向量化）
  │           │     │     └── config.py
  │           │     └── config.py
  │           └── schemas.py
  └── rag_manager.py（启动时加载文档）
```

## 关键概念解释

### 什么是 RAG？
RAG = Retrieval-Augmented Generation（检索增强生成）。
简单说：先从你的文档库里找到相关内容，再把这些内容喂给 LLM，让它基于你的数据回答问题。
没有 RAG，LLM 只能用它训练时学到的知识；有了 RAG，LLM 能回答你私有文档里的问题。

### 什么是向量化（Embedding）？
把文本转成一组数字（向量），语义相近的文本，向量也相近。
比如 "价格方案" 和 "基础版：¥99/月" 的向量距离很近，所以能被检索到。

### 什么是 FAISS？
Facebook 开源的向量相似度搜索库。存储所有文档块的向量，查询时快速找到最相似的几个。

### 什么是 LangGraph 状态图？
把 Agent 的工作流程定义成一个有向图：节点是处理步骤，边是执行顺序。
AgentState 是在节点间传递的数据容器，每个节点读取状态、处理、写回状态。
```
