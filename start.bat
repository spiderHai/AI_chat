@echo off
REM AI Chat 应用启动脚本 (Windows)

echo 🚀 启动 AI Chat 应用...

REM 启动后端
echo 📦 启动后端服务...
cd backend
if not exist venv (
    python -m venv venv
)
call venv\Scripts\activate.bat
pip install -q -r requirements.txt
start "AI Chat Backend" uvicorn main:app --reload --host 0.0.0.0 --port 8000
echo ✅ 后端服务启动

REM 等待后端启动
timeout /t 3 /nobreak

REM 启动前端
echo 📱 启动前端服务...
cd ..\frontend
if not exist node_modules (
    npm install -q
)
start "AI Chat Frontend" npm run dev
echo ✅ 前端服务启动

echo.
echo 🎉 应用已启动！
echo 📍 前端: http://localhost:3000
echo 📍 后端: http://localhost:8000
echo 📍 API 文档: http://localhost:8000/docs
echo.
echo 关闭命令窗口以停止服务
pause
