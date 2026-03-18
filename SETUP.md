# 项目配置说明

## 环境变量配置

### 后端 (.env)
```
DASHSCOPE_API_KEY=your_api_key_here
```

### 前端 (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 快速启动

### 方式 1: 使用启动脚本

**Windows:**
```bash
start.bat
```

**Linux/Mac:**
```bash
bash start.sh
```

### 方式 2: 手动启动

**后端:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**前端:**
```bash
cd frontend
npm install
npm run dev
```

### 方式 3: 使用 Docker

```bash
docker-compose up
```

## 项目结构

```
AI_Chat/
├── backend/
│   ├── main.py              # 主应用
│   ├── config.py            # 配置文件
│   ├── models.py            # 数据模型
│   ├── requirements.txt      # Python 依赖
│   ├── .env                 # 环境变量
│   ├── Dockerfile           # Docker 配置
│   └── test_main.py         # 测试文件
├── frontend/
│   ├── app/
│   │   ├── page.tsx         # 主页面
│   │   ├── layout.tsx       # 布局
│   │   └── globals.css      # 全局样式
│   ├── lib/
│   │   ├── api.ts           # API 调用
│   │   └── utils.ts         # 工具函数
│   ├── types/
│   │   └── index.ts         # 类型定义
│   ├── package.json         # Node 依赖
│   ├── .env.local           # 环境变量
│   └── Dockerfile           # Docker 配置
├── docker-compose.yml       # Docker Compose 配置
├── start.sh                 # Linux/Mac 启动脚本
├── start.bat                # Windows 启动脚本
└── README.md                # 项目文档
```

## API 端点

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| POST | `/api/chat` | 聊天接口 |
| POST | `/api/chat/stream` | 流式聊天 |

## 访问地址

- 前端: http://localhost:3000
- 后端: http://localhost:8000
- API 文档: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 故障排除

### 后端无法启动
- 检查 Python 版本 >= 3.8
- 检查 DASHSCOPE_API_KEY 是否正确设置
- 查看错误日志

### 前端无法连接后端
- 确保后端服务正在运行
- 检查 .env.local 中的 API_URL
- 检查浏览器控制台错误

### CORS 错误
- 确保前端地址在后端 CORS 配置中
- 检查 config.py 中的 cors_origins

## 开发建议

1. 使用虚拟环境隔离 Python 依赖
2. 定期更新依赖包
3. 编写单元测试
4. 使用 TypeScript 确保类型安全
5. 遵循代码规范和最佳实践
