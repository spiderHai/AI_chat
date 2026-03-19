# RAG 快速启动指南

## 🚀 5 分钟上手 RAG

### 1. 安装依赖

```bash
cd backend
pip install pymilvus fastapi uvicorn requests python-dotenv
```

### 2. 启动服务

```bash
python simple_rag.py
```

服务将在 `http://localhost:8001` 启动

### 3. 添加文档

```bash
curl -X POST http://localhost:8001/add \
  -H "Content-Type: application/json" \
  -d '{
    "text": "我们公司提供 AI 聊天机器人服务，支持智能客服、知识库管理等功能。",
    "title": "产品介绍"
  }'
```

### 4. 测试查询

```bash
curl -X POST http://localhost:8001/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "你们提供什么服务？",
    "top_k": 3
  }'
```

### 5. 使用测试脚本

```bash
python test_rag.py
```

## 📁 文件说明

- `simple_rag.py` - 简化版 RAG 实现（推荐新手）
- `langgraph_rag_agent.py` - 完整版 RAG Agent（高级功能）
- `test_rag.py` - 测试脚本
- `documents/sample_docs.txt` - 示例文档

## 🔑 核心概念

**RAG = 检索 + 增强 + 生成**

1. **检索**：从向量数据库找相关文档
2. **增强**：将文档作为上下文
3. **生成**：LLM 基于上下文回答

## 📊 API 接口

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

### GET /stats - 统计信息

## 💡 使用建议

1. 先添加 3-5 个测试文档
2. 尝试不同的问题
3. 观察返回的来源（sources）
4. 调整 top_k 参数（1-5）

## 🎯 下一步

- 阅读 [RAG_SIMPLE_GUIDE.md](RAG_SIMPLE_GUIDE.md) 了解原理
- 查看 [langgraph_rag_agent.py](backend/langgraph_rag_agent.py) 学习高级用法
- 集成到前端界面

---

**问题？** 查看 RAG_SIMPLE_GUIDE.md 获取详细说明
