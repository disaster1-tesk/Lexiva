#!/usr/bin/env python3
"""
Lexiva 跨平台启动脚本
支持 Windows / macOS / Linux，自动检测平台并适配
"""

import os
import sys
import subprocess
import shutil
import platform
import argparse
from pathlib import Path

# ─── 配置 ────────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).parent.resolve()
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

BACKEND_PORT = 8000
FRONTEND_PORT = 5173

# ─── 工具函数 ────────────────────────────────────────────────────────────────


def color(code: str, text: str) -> str:
    """跨平台着色（Windows PowerShell 不支持 ANSI，直接返回原文本）"""
    if platform.system() == "Windows" and os.environ.get("TERM") != "xterm-256color":
        return text
    return f"\033[{code}m{text}\033[0m"


def green(text: str) -> str:
    return color("32", text)


def yellow(text: str) -> str:
    return color("33", text)


def red(text: str) -> str:
    return color("31", text)


def print_banner():
    print(green("======================================"))
    print(green("     Lexiva AI 英语学习系统"))
    print(green("======================================"))
    print(f"  平台: {platform.system()} {platform.release()}")
    print(f"  Python: {platform.python_version()}")
    print()


def get_venv_python(venv_dir: Path) -> Path:
    """获取虚拟环境中 python 可执行文件路径（跨平台）"""
    if platform.system() == "Windows":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def get_venv_activate(venv_dir: Path) -> Path | str:
    """获取虚拟环境激活脚本路径"""
    if platform.system() == "Windows":
        return venv_dir / "Scripts" / "activate.bat"
    return venv_dir / "bin" / "activate"


def ensure_venv(venv_dir: Path):
    """确保虚拟环境存在，不存在则创建"""
    if not venv_dir.exists():
        print(yellow(f"  创建虚拟环境: {venv_dir}"))
        subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
    else:
        print(f"  虚拟环境已存在: {venv_dir}")


def pip_install(venv_python: Path, requirements: Path):
    """在虚拟环境中安装依赖"""
    print(yellow("  安装依赖..."))
    # 使用清华镜像 + 跳过代理验证
    pip_args = [
        str(venv_python), "-m", "pip", "install",
        "-i", "https://pypi.tuna.tsinghua.edu.cn/simple",
        "--trusted-host", "pypi.tuna.tsinghua.edu.cn",
        "-r", str(requirements), "-q"
    ]
    subprocess.run(pip_args, check=True)


def check_command(cmd: str) -> bool:
    """检查命令是否存在"""
    return shutil.which(cmd) is not None


def get_command_path(cmd: str) -> str:
    """获取命令的完整路径"""
    path = shutil.which(cmd)
    return path if path else cmd


def check_docker() -> bool:
    """检查 Docker 是否可用"""
    return check_command("docker") and check_command("docker-compose")


# ─── 后端启动 ────────────────────────────────────────────────────────────────


def start_backend_local():
    """本地启动后端（FastAPI）"""
    print(yellow("\n[1/2] 正在启动后端服务..."))
    venv_dir = BACKEND_DIR / "venv"
    ensure_venv(venv_dir)
    venv_python = get_venv_python(venv_dir)
    requirements = BACKEND_DIR / "requirements.txt"

    pip_install(venv_python, requirements)

    print(green("  后端服务启动中: http://localhost:8000"))
    print(green("  API 文档: http://localhost:8000/docs\n"))

    subprocess.run(
        [
            str(venv_python), "-m", "uvicorn", "main:app",
            "--host", "0.0.0.0", "--port", str(BACKEND_PORT),
        ],
        cwd=str(BACKEND_DIR),
    )


def start_frontend_local():
    """本地启动前端（Vite）"""
    print(yellow("\n[2/2] 正在启动前端服务..."))

    if not check_command("npm"):
        print(red("  错误: npm 未安装，请先安装 Node.js (https://nodejs.org/)"))
        sys.exit(1)

    if not (FRONTEND_DIR / "node_modules").exists():
        print(yellow("  安装前端依赖..."))
        subprocess.run([get_command_path("npm"), "install"], cwd=str(FRONTEND_DIR), check=True)

    print(green(f"  前端服务启动中: http://localhost:{FRONTEND_PORT}\n"))

    subprocess.run(
        [get_command_path("npm"), "run", "dev", "--", "--host", "0.0.0.0", "--port", str(FRONTEND_PORT)],
        cwd=str(FRONTEND_DIR),
    )


# ─── Docker 启动 ─────────────────────────────────────────────────────────────


def start_docker():
    """使用 Docker Compose 启动"""
    print(yellow("\n使用 Docker 启动服务..."))

    if not check_docker():
        print(red("  错误: Docker 或 Docker Compose 未安装"))
        print("  请访问 https://docs.docker.com/get-docker/ 安装 Docker")
        sys.exit(1)

    env_file = BACKEND_DIR / ".env"
    env_example = BACKEND_DIR / ".env.example"
    if not env_file.exists() and env_example.exists():
        print(yellow("  创建 .env 配置文件..."))
        shutil.copy(env_example, env_file)
        print(yellow("  请编辑 backend/.env 填入您的 API Keys"))

    print(yellow("  构建并启动容器..."))
    subprocess.run([get_command_path("docker-compose"), "up", "-d", "--build"], cwd=PROJECT_ROOT)

    print(green("\n服务已启动:"))
    print(f"  - 后端: http://localhost:{BACKEND_PORT}")
    print(f"  - 前端: http://localhost:{FRONTEND_PORT}")
    print(f"  - API 文档: http://localhost:{BACKEND_PORT}/docs")


def stop_docker():
    """停止 Docker 服务"""
    print(yellow("\n停止 Docker 服务..."))
    subprocess.run([get_command_path("docker-compose"), "down"], cwd=PROJECT_ROOT)


# ─── 同时启动前后端 ──────────────────────────────────────────────────────────


def start_all_local():
    """同时启动前后端"""
    import threading
    import time

    print(yellow("\n启动后端..."))
    t_backend = threading.Thread(target=start_backend_local, daemon=True)
    t_backend.start()
    time.sleep(2)  # 等待后端先启动

    print(yellow("启动前端...\n"))
    start_frontend_local()


# ─── 主入口 ──────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Lexiva 启动脚本")
    parser.add_argument(
        "command",
        nargs="?",
        default="help",
        choices=["docker", "docker:build", "docker:stop", "backend", "frontend", "all", "help"],
        help="启动命令",
    )
    args = parser.parse_args()

    print_banner()

    if args.command == "docker":
        start_docker()
    elif args.command == "docker:build":
        if not check_docker():
            print(red("  错误: Docker 未安装"))
            sys.exit(1)
        subprocess.run([get_command_path("docker-compose"), "build"], cwd=PROJECT_ROOT)
    elif args.command == "docker:stop":
        stop_docker()
    elif args.command == "backend":
        start_backend_local()
    elif args.command == "frontend":
        start_frontend_local()
    elif args.command == "all":
        start_all_local()
    else:
        print("用法: python run.py [命令]")
        print()
        print("命令:")
        print("  docker        使用 Docker 启动（推荐）")
        print("  docker:build  构建 Docker 镜像")
        print("  docker:stop  停止 Docker 服务")
        print("  backend       本地启动后端")
        print("  frontend      本地启动前端")
        print("  all           本地启动前后端")
        print()
        print("示例:")
        print("  python run.py all        # Windows/Mac/Linux 通用")
        print("  ./run.sh docker          # Unix 系统也可用 shell 脚本")


if __name__ == "__main__":
    main()
