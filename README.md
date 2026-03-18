# AI Chat Application

一个基于 FastAPI 后端和 Next.js 前端的 AI 聊天应用，集成了阿里云通义千问大模型。

## 项目结构

```
AI_Chat/
├── backend/          # FastAPI 后端
│   ├── main.py      # 主应用文件
│   ├── requirements.txt
│   └── .env         # 环境变量配置
└── frontend/        # Next.js 前端
    ├── app/         # 应用页面
    ├── lib/         # 工具库
    ├── package.json
    └── .env.local   # 环境变量配置
```

## 快速开始

### 后端设置

1. 进入后端目录：
```bash
cd backend
```

2. 创建虚拟环境：
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 配置环境变量（.env 文件）：
```
DASHSCOPE_API_KEY=your_api_key_here
```

5. 启动后端服务：
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

后端将在 `http://localhost:8000` 运行

### 前端设置

1. 进入前端目录：
```bash
cd frontend
```

2. 安装依赖：
```bash
npm install
```

3. 启动开发服务器：
```bash
npm run dev
```

前端将在 `http://localhost:3000` 运行

## API 接口

### 健康检查
- **GET** `/api/health`
- 返回服务器状态

### 聊天接口
- **POST** `/api/chat`
- 请求体：
```json
{
  "question": "你的问题"
}
```
- 响应：
```json
{
  "answer": "AI 的回答",
  "timestamp": "2024-03-17T10:30:00"
}
```

## 功能特性

- ✅ 实时聊天界面
- ✅ 消息历史记录
- ✅ 加载状态指示
- ✅ 错误处理
- ✅ 深色模式支持
- ✅ 响应式设计
- ✅ CORS 跨域支持

## 技术栈

### 后端
- FastAPI - 现代 Python Web 框架
- Uvicorn - ASGI 服务器
- LangChain - LLM 集成框架
- Pydantic - 数据验证

### 前端
- Next.js 16 - React 框架
- React 19 - UI 库
- TypeScript - 类型安全
- Tailwind CSS - 样式框架

## 环境要求

- Python 3.8+
- Node.js 18+
- npm 或 yarn

## 故障排除

### 后端连接失败
- 确保后端服务正在运行：`http://localhost:8000/api/health`
- 检查 CORS 配置是否正确
- 验证 API 密钥是否有效

### 前端无法连接后端
- 检查 `.env.local` 中的 `NEXT_PUBLIC_API_URL`
- 确保后端服务器地址正确
- 检查浏览器控制台的错误信息

## 许可证

MIT
