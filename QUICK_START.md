# 项目快速参考

## 🚀 快速启动

### Windows
```bash
start.bat
```

### Linux/Mac
```bash
bash start.sh
```

### Docker
```bash
docker-compose up
```

## 📍 访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端 | http://localhost:3000 | 聊天界面 |
| 后端 | http://localhost:8000 | API 服务 |
| API 文档 | http://localhost:8000/docs | Swagger UI |
| ReDoc | http://localhost:8000/redoc | ReDoc 文档 |

## 📝 常用命令

### 后端
```bash
# 启动开发服务器
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 运行测试
pytest test_main.py -v

# 查看 API 文档
# 访问 http://localhost:8000/docs
```

### 前端
```bash
# 启动开发服务器
cd frontend
npm run dev

# 构建生产版本
npm run build

# 启动生产服务器
npm start

# 运行 linter
npm run lint
```

## 🔧 环境变量

### 后端 (backend/.env)
```env
DASHSCOPE_API_KEY=your_api_key_here
```

### 前端 (frontend/.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 📂 项目结构

```
AI_Chat/
├── backend/              # FastAPI 后端
├── frontend/             # Next.js 前端
├── docker-compose.yml    # Docker 编排
├── start.sh             # Linux/Mac 启动脚本
├── start.bat            # Windows 启动脚本
├── init.py              # 初始化脚本
├── verify.py            # 验证脚本
├── README.md            # 项目说明
├── SETUP.md             # 配置指南
├── GUIDE.md             # 完整指南
└── QUICK_START.md       # 本文件
```

## 🐛 常见问题

### Q: 后端无法启动
A: 检查 Python 版本 >= 3.8，运行 `pip install -r requirements.txt`

### Q: 前端无法连接后端
A: 检查 `.env.local` 中的 API_URL，确保后端服务运行

### Q: CORS 错误
A: 编辑 `backend/config.py`，添加前端地址到 `cors_origins`

### Q: API Key 无效
A: 检查 `.env` 中的 DASHSCOPE_API_KEY 是否正确

## 📚 文档

- [README.md](README.md) - 项目概述
- [SETUP.md](SETUP.md) - 详细配置
- [GUIDE.md](GUIDE.md) - 完整指南

## 🔗 相关链接

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Next.js 文档](https://nextjs.org/docs)
- [阿里云 DashScope](https://dashscope.aliyun.com/)

---

**提示:** 运行 `python verify.py` 验证项目结构
