# AI Chat 项目完整指南

## 📋 项目概述

AI Chat 是一个现代化的聊天应用，集成了阿里云通义千问大模型。采用 FastAPI 后端和 Next.js 前端的架构，提供实时聊天、消息历史、错误处理等功能。

## 🏗️ 项目架构

```
┌─────────────────────────────────────────────────────┐
│                   Next.js 前端                       │
│              (React 19 + TypeScript)                │
│         http://localhost:3000                       │
└────────────────────┬────────────────────────────────┘
                     │ HTTP/REST
                     ▼
┌─────────────────────────────────────────────────────┐
│                  FastAPI 后端                        │
│            (Python 3.8+ + Uvicorn)                  │
│         http://localhost:8000                       │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
            ┌────────────────────┐
            │  通义千问 LLM API   │
            │  (阿里云 DashScope)│
            └────────────────────┘
```

## 📁 项目结构详解

```
AI_Chat/
├── backend/                    # FastAPI 后端应用
│   ├── main.py                # 主应用入口
│   ├── config.py              # 配置管理
│   ├── models.py              # Pydantic 数据模型
│   ├── requirements.txt        # Python 依赖
│   ├── .env                   # 环境变量（需配置）
│   ├── Dockerfile             # Docker 镜像配置
│   └── test_main.py           # 单元测试
│
├── frontend/                   # Next.js 前端应用
│   ├── app/
│   │   ├── page.tsx           # 主页面
│   │   ├── layout.tsx         # 根布局
│   │   └── globals.css        # 全局样式
│   ├── components/
│   │   └── ChatComponent.tsx  # 聊天组件
│   ├── lib/
│   │   ├── api.ts             # API 调用函数
│   │   └── utils.ts           # 工具函数
│   ├── types/
│   │   └── index.ts           # TypeScript 类型定义
│   ├── package.json           # Node 依赖
│   ├── .env.local             # 环境变量（需配置）
│   ├── Dockerfile             # Docker 镜像配置
│   └── tsconfig.json          # TypeScript 配置
│
├── docker-compose.yml         # Docker Compose 编排
├── start.sh                   # Linux/Mac 启动脚本
├── start.bat                  # Windows 启动脚本
├── init.py                    # 项目初始化脚本
├── README.md                  # 项目说明
├── SETUP.md                   # 详细配置指南
├── .gitignore                 # Git 忽略文件
└── GUIDE.md                   # 本文件
```

## 🚀 快速开始

### 前置要求

- Python 3.8+
- Node.js 18+
- npm 或 yarn
- 阿里云 DashScope API Key

### 方式 1: 自动启动（推荐）

**Windows:**
```bash
start.bat
```

**Linux/Mac:**
```bash
bash start.sh
```

### 方式 2: 手动启动

**后端启动:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**前端启动（新终端）:**
```bash
cd frontend
npm install
npm run dev
```

### 方式 3: Docker 启动

```bash
docker-compose up
```

## ⚙️ 环境配置

### 后端配置 (backend/.env)

```env
DASHSCOPE_API_KEY=sk-your-api-key-here
```

获取 API Key：
1. 访问 https://dashscope.aliyun.com
2. 注册/登录账户
3. 创建 API Key
4. 复制到 .env 文件

### 前端配置 (frontend/.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 📡 API 接口文档

### 1. 健康检查

**请求:**
```http
GET /api/health
```

**响应:**
```json
{
  "status": "ok",
  "timestamp": "2024-03-17T10:30:00.123456"
}
```

### 2. 聊天接口

**请求:**
```http
POST /api/chat
Content-Type: application/json

{
  "question": "你好，请介绍一下自己"
}
```

**响应:**
```json
{
  "answer": "你好！我是通义千问，一个由阿里云开发的大型语言模型...",
  "timestamp": "2024-03-17T10:30:05.123456"
}
```

**错误响应:**
```json
{
  "detail": "Question cannot be empty"
}
```

### 3. 流式聊天接口

**请求:**
```http
POST /api/chat/stream
Content-Type: application/json

{
  "question": "你好"
}
```

## 🎨 前端功能

- ✅ 实时聊天界面
- ✅ 消息历史记录
- ✅ 加载状态指示
- ✅ 错误提示和处理
- ✅ 连接状态显示
- ✅ 深色模式支持
- ✅ 响应式设计
- ✅ 自动滚动到最新消息

## 🔧 后端功能

- ✅ FastAPI 框架
- ✅ CORS 跨域支持
- ✅ 数据验证（Pydantic）
- ✅ 错误处理
- ✅ 环境变量管理
- ✅ 自动 API 文档（Swagger UI）
- ✅ 单元测试支持

## 📊 技术栈详情

### 后端
| 技术 | 版本 | 用途 |
|------|------|------|
| FastAPI | 0.104.1 | Web 框架 |
| Uvicorn | 0.24.0 | ASGI 服务器 |
| Pydantic | 2.5.0 | 数据验证 |
| LangChain | 0.1.0 | LLM 集成 |
| Python-dotenv | 1.0.0 | 环境变量 |

### 前端
| 技术 | 版本 | 用途 |
|------|------|------|
| Next.js | 16.1.7 | React 框架 |
| React | 19.2.3 | UI 库 |
| TypeScript | 5.x | 类型安全 |
| Tailwind CSS | 4.x | 样式框架 |

## 🧪 测试

### 运行后端测试

```bash
cd backend
pip install pytest
pytest test_main.py -v
```

### 测试 API

使用 Swagger UI：
```
http://localhost:8000/docs
```

或使用 curl：
```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"question":"你好"}'
```

## 🐛 故障排除

### 问题 1: 后端无法启动

**症状:** `ModuleNotFoundError` 或 `ImportError`

**解决方案:**
```bash
cd backend
pip install --upgrade -r requirements.txt
```

### 问题 2: 前端无法连接后端

**症状:** 发送消息后无响应或显示错误

**检查清单:**
- [ ] 后端服务正在运行 (`http://localhost:8000/api/health`)
- [ ] `.env.local` 中的 API_URL 正确
- [ ] 浏览器控制台无 CORS 错误
- [ ] 防火墙未阻止 8000 端口

### 问题 3: CORS 错误

**症状:** 浏览器控制台显示 CORS 错误

**解决方案:**
编辑 `backend/config.py`，添加前端地址到 `cors_origins`：
```python
cors_origins: list = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://your-domain.com"
]
```

### 问题 4: API Key 无效

**症状:** 聊天返回 401 或认证错误

**解决方案:**
1. 检查 `.env` 中的 API Key 是否正确
2. 确保 API Key 未过期
3. 访问 DashScope 控制台验证 API Key 状态

## 📈 性能优化建议

1. **后端优化:**
   - 使用异步处理
   - 添加请求缓存
   - 实现速率限制
   - 使用连接池

2. **前端优化:**
   - 代码分割
   - 图片优化
   - 缓存策略
   - 虚拟滚动（大量消息时）

## 🔐 安全建议

1. **环境变量:**
   - 不要提交 `.env` 文件到 Git
   - 使用强密码和 API Key
   - 定期轮换 API Key

2. **API 安全:**
   - 实现身份验证
   - 添加速率限制
   - 验证输入数据
   - 使用 HTTPS

3. **前端安全:**
   - 防止 XSS 攻击
   - 验证用户输入
   - 使用 Content Security Policy

## 📚 相关资源

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Next.js 文档](https://nextjs.org/docs)
- [LangChain 文档](https://python.langchain.com/)
- [阿里云 DashScope](https://dashscope.aliyun.com/)
- [Tailwind CSS](https://tailwindcss.com/)

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📝 许可证

MIT License - 详见 LICENSE 文件

## 📞 支持

如有问题或建议，请提交 Issue 或 Pull Request。

---

**最后更新:** 2024-03-17
**版本:** 1.0.0
