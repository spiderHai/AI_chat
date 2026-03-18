#!/bin/bash

# AI Chat 应用启动脚本

echo "🚀 启动 AI Chat 应用..."

# 启动后端
echo "📦 启动后端服务..."
cd backend
python -m venv venv 2>/dev/null || true
source venv/bin/activate 2>/dev/null || . venv/Scripts/activate 2>/dev/null || true
pip install -q -r requirements.txt 2>/dev/null || true
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo "✅ 后端服务启动 (PID: $BACKEND_PID)"

# 等待后端启动
sleep 3

# 启动前端
echo "📱 启动前端服务..."
cd ../frontend
npm install -q 2>/dev/null || true
npm run dev &
FRONTEND_PID=$!
echo "✅ 前端服务启动 (PID: $FRONTEND_PID)"

echo ""
echo "🎉 应用已启动！"
echo "📍 前端: http://localhost:3000"
echo "📍 后端: http://localhost:8000"
echo "📍 API 文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 等待用户中断
wait
