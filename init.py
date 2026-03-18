"""
项目初始化脚本
"""
import os
import sys
from pathlib import Path


def create_directories():
    """创建必要的目录"""
    dirs = [
        "backend",
        "frontend/lib",
        "frontend/types",
        "frontend/components",
    ]
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    print("✅ 目录创建完成")


def check_requirements():
    """检查环境要求"""
    print("\n📋 检查环境要求...")

    # 检查 Python
    try:
        import sys
        version = sys.version_info
        if version.major >= 3 and version.minor >= 8:
            print(f"✅ Python {version.major}.{version.minor} 已安装")
        else:
            print(f"❌ Python 版本过低，需要 3.8+")
            return False
    except Exception as e:
        print(f"❌ Python 检查失败: {e}")
        return False

    # 检查 Node.js
    try:
        import subprocess
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Node.js {result.stdout.strip()} 已安装")
        else:
            print("❌ Node.js 未安装")
            return False
    except Exception as e:
        print(f"❌ Node.js 检查失败: {e}")
        return False

    return True


def print_next_steps():
    """打印后续步骤"""
    print("\n" + "="*50)
    print("🎉 项目初始化完成！")
    print("="*50)
    print("\n📚 后续步骤：")
    print("\n1️⃣  配置环境变量")
    print("   - 编辑 backend/.env，添加 DASHSCOPE_API_KEY")
    print("   - 编辑 frontend/.env.local，配置 API_URL")
    print("\n2️⃣  启动应用")
    print("   Windows: start.bat")
    print("   Linux/Mac: bash start.sh")
    print("   Docker: docker-compose up")
    print("\n3️⃣  访问应用")
    print("   前端: http://localhost:3000")
    print("   后端: http://localhost:8000")
    print("   API 文档: http://localhost:8000/docs")
    print("\n📖 更多信息请查看 README.md 和 SETUP.md")
    print("="*50 + "\n")


if __name__ == "__main__":
    print("🚀 初始化 AI Chat 项目...\n")

    if not check_requirements():
        print("\n❌ 环境检查失败，请安装必要的依赖")
        sys.exit(1)

    create_directories()
    print_next_steps()
