"""
项目验证脚本
"""
import os
import sys
from pathlib import Path

# 设置编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def check_backend_structure():
    """检查后端项目结构"""
    print("\n[后端] 检查结构...")
    backend_files = [
        "backend/main.py",
        "backend/config.py",
        "backend/models.py",
        "backend/requirements.txt",
        "backend/.env",
    ]

    missing = []
    for file in backend_files:
        if not Path(file).exists():
            missing.append(file)
        else:
            print(f"  OK {file}")

    if missing:
        print(f"  MISSING: {', '.join(missing)}")
        return False
    return True


def check_frontend_structure():
    """检查前端项目结构"""
    print("\n[前端] 检查结构...")
    frontend_files = [
        "frontend/app/page.tsx",
        "frontend/app/layout.tsx",
        "frontend/components/ChatComponent.tsx",
        "frontend/lib/api.ts",
        "frontend/lib/utils.ts",
        "frontend/types/index.ts",
        "frontend/package.json",
        "frontend/.env.local",
    ]

    missing = []
    for file in frontend_files:
        if not Path(file).exists():
            missing.append(file)
        else:
            print(f"  OK {file}")

    if missing:
        print(f"  MISSING: {', '.join(missing)}")
        return False
    return True


def check_config_files():
    """检查配置文件"""
    print("\n[配置] 检查文件...")
    config_files = [
        "docker-compose.yml",
        "README.md",
        "SETUP.md",
        "GUIDE.md",
        ".gitignore",
    ]

    missing = []
    for file in config_files:
        if not Path(file).exists():
            missing.append(file)
        else:
            print(f"  OK {file}")

    if missing:
        print(f"  MISSING: {', '.join(missing)}")
        return False
    return True


def check_env_files():
    """检查环境变量文件"""
    print("\n[环境] 检查配置...")

    # 检查后端 .env
    backend_env = Path("backend/.env")
    if backend_env.exists():
        with open(backend_env, encoding='utf-8') as f:
            content = f.read()
            if "DASHSCOPE_API_KEY" in content:
                print("  OK backend/.env configured")
            else:
                print("  WARNING backend/.env missing DASHSCOPE_API_KEY")
    else:
        print("  MISSING backend/.env")

    # 检查前端 .env.local
    frontend_env = Path("frontend/.env.local")
    if frontend_env.exists():
        with open(frontend_env, encoding='utf-8') as f:
            content = f.read()
            if "NEXT_PUBLIC_API_URL" in content:
                print("  OK frontend/.env.local configured")
            else:
                print("  WARNING frontend/.env.local missing NEXT_PUBLIC_API_URL")
    else:
        print("  MISSING frontend/.env.local")


def print_summary(backend_ok, frontend_ok, config_ok):
    """打印总结"""
    print("\n" + "="*60)
    print("Project Verification Summary")
    print("="*60)

    print(f"\nBackend:  {'PASS' if backend_ok else 'FAIL'}")
    print(f"Frontend: {'PASS' if frontend_ok else 'FAIL'}")
    print(f"Config:   {'PASS' if config_ok else 'FAIL'}")

    if backend_ok and frontend_ok and config_ok:
        print("\nStatus: All checks passed!")
        print("\nNext steps:")
        print("  1. Configure environment variables if needed")
        print("  2. Run start.bat (Windows) or bash start.sh (Linux/Mac)")
        print("  3. Visit http://localhost:3000")
    else:
        print("\nStatus: Some checks failed, please review above")

    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    print("Starting project verification...\n")

    backend_ok = check_backend_structure()
    frontend_ok = check_frontend_structure()
    config_ok = check_config_files()

    check_env_files()

    print_summary(backend_ok, frontend_ok, config_ok)
