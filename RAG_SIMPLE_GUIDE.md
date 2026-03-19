# RAG 技术简明指南

## 什么是 RAG？

**RAG (Retrieval-Augmented Generation)** = 检索 + 增强 + 生成

传统 AI 只能基于训练数据回答，RAG 可以：
1. **检索**外部知识库
2. **增强**上下文
3. **生成**准确答案

## RAG 工作流程

```
用户提问
   ↓
[1] 问题向量化 (Embedding)
   ↓
[2] 向量数据库检索相似文档
   ↓
[3] 构建上下文 (检索到的文档)
   ↓
[4] LLM 基于上下文生成答案
   ↓
返回答案 + 来源
```

## 核心组件

### 1. Embedding (向量化)
将文本转换为数字向量，相似的文本向量距离近。

```python
# 使用 DashScope Embedding API
text = "人工智能是什么？"
vector = get_embedding(text)  # 返回 1536 维向量
```

### 2. 向量数据库
存储和检索向量，本项目使用 **Milvus Lite**（轻量级，无需独立服务）。

```python
# 插入文档
milvus_client.insert(collection, {
    "vector": vector,
    "text": "文档内容"
})

# 检索相似文档
results = milvus_client.search(
    data=[query_vector],
    limit=3  # 返回最相似的 3 个
)
```

### 3. LLM 生成
基于检索到的文档生成答案。

```python
prompt = f"""
文档: {retrieved_docs}
问题: {question}
请基于文档回答。
"""
answer = call_llm(prompt)
```

## 项目实现

### 文件说明
- `simple_rag.py` - 简化版 RAG 实现（推荐）
- `langgraph_rag_agent.py` - 完整版 RAG Agent

### 快速开始

1. **安装依赖**
```bash
pip install pymilvus fastapi uvicorn requests python-dotenv
```

2. **启动服务**
```bash
cd backend
python simple_rag.py
```

3. **添加文档**
```bash
curl -X POST http://localhost:8001/add \
  -H "Content-Type: application/json" \
  -d '{
    "text": "我们公司提供 AI 聊天机器人服务，支持多语言对话。",
    "title": "公司介绍"
  }'
```

4. **查询**
```bash
curl -X POST http://localhost:8001/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "你们提供什么服务？",
    "top_k": 3
  }'
```

## API 接口

### POST /add - 添加文档
```json
{
  "text": "文档内容",
  "title": "文档标题"
}
```

### POST /query - RAG 查询
```json
{
  "question": "用户问题",
  "top_k": 3
}
```

响应：
```json
{
  "answer": "基于文档的回答",
  "sources": [
    {"title": "文档1", "score": 0.95}
  ]
}
```

### GET /stats - 统计信息
返回文档总数等信息。

## RAG vs 传统 LLM

| 特性 | 传统 LLM | RAG |
|------|---------|-----|
| 知识来源 | 训练数据 | 外部文档 |
| 更新成本 | 重新训练 | 添加文档 |
| 准确性 | 可能幻觉 | 基于真实文档 |
| 可追溯 | 无 | 有来源 |

## 优化建议

1. **文档分块**：长文档切分成 500-1000 字的块
2. **混合检索**：结合关键词和向量检索
3. **重排序**：对检索结果重新排序
4. **缓存**：缓存常见问题的向量

## 常见问题

**Q: 为什么使用 Milvus Lite？**
A: 轻量级，无需独立服务，适合开发和小规模部署。

**Q: 向量维度是什么？**
A: DashScope text-embedding-v1 返回 1536 维向量。

**Q: 如何提高检索准确性？**
A: 增加文档质量、调整 top_k 参数、使用更好的 embedding 模型。

## 下一步

- 添加更多文档测试效果
- 尝试不同的 top_k 值
- 集成到前端界面
- 添加文档管理功能

---

**技术栈**
- FastAPI - Web 框架
- Milvus Lite - 向量数据库
- DashScope - Embedding + LLM
- Python 3.8+
