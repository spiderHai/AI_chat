from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import requests
from datetime import datetime
from pydantic import BaseModel

# 加载环境变量
load_dotenv()

# 初始化FastAPI
app = FastAPI(title="AI Chat API", version="1.0.0")

# 解决跨域（前端Next.js默认端口3000）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DashScope API 配置
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
DASHSCOPE_API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"

# 定义请求体模型
class QueryRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    answer: str
    timestamp: str

class HealthResponse(BaseModel):
    status: str
    timestamp: str


# 健康检查
@app.get("/api/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="ok",
        timestamp=datetime.now().isoformat()
    )

# 简单问答接口
@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: QueryRequest):
    try:
        if not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")

        if not DASHSCOPE_API_KEY:
            raise HTTPException(status_code=500, detail="API Key not configured")

        # 调用 DashScope API - 使用正确的格式
        headers = {
            "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "qwen-turbo",
            "input": {
                "messages": [
                    {"role": "user", "content": request.question}
                ]
            },
            "parameters": {}
        }

        response = requests.post(
            DASHSCOPE_API_URL,
            json=payload,
            headers=headers,
            timeout=30
        )

        if response.status_code != 200:
            error_detail = response.text
            print(f"API Error: {response.status_code}, {error_detail}")
            raise HTTPException(
                status_code=500,
                detail=f"API Error: {response.status_code}"
            )

        result = response.json()

        # 提取答案
        if "output" in result and "text" in result["output"]:
            answer = result["output"]["text"]
        else:
            answer = "Unable to get response from AI"

        return ChatResponse(
            answer=answer,
            timestamp=datetime.now().isoformat()
        )
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Request timeout")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 流式聊天接口
@app.post("/api/chat/stream")
async def chat_stream(request: QueryRequest):
    try:
        if not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")

        if not DASHSCOPE_API_KEY:
            raise HTTPException(status_code=500, detail="API Key not configured")

        headers = {
            "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "qwen-turbo",
            "input": {
                "messages": [
                    {"role": "user", "content": request.question}
                ]
            },
            "parameters": {}
        }

        response = requests.post(
            DASHSCOPE_API_URL,
            json=payload,
            headers=headers,
            timeout=30
        )

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"API Error: {response.status_code}")

        result = response.json()

        if "output" in result and "text" in result["output"]:
            answer = result["output"]["text"]
        else:
            answer = "Unable to get response from AI"

        return ChatResponse(
            answer=answer,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 启动命令：uvicorn main:app --reload --host 0.0.0.0 --port 8000
