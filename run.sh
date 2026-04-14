#!/bin/bash

# Lexiva 启动脚本
# 支持 Docker 和本地两种启动方式

set -e

# 颜色定义
RED='\n033[0;31m'
GREEN='\n033[0;32m'
YELLOW='\n033[1;33m'
NC='\n033[0m' # No Color

echo -e \"${GREEN}======================================${NC}\"
echo -e \"${GREEN}     Lexiva AI 英语学习系统${NC}\"
echo -e \"${GREEN}======================================${NC}\"

# 检查 Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e \"${RED}错误: Docker 未安装${NC}\"
        echo \"请访问 https://docs.docker.com/get-docker/\"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        echo -e \"${RED}错误: Docker Compose 未安装${NC}\"
        echo \"请访问 https://docs.docker.com/compose/install/\"
        exit 1
    fi
}

# 本地启动后端
start_backend_local() {
    echo -e \"${YELLOW}正在启动后端服务...${NC}\"

    cd backend

    # 检查虚拟环境
    if [ ! -d \"venv\" ]; then
        echo \"创建虚拟环境...\"
        python3 -m venv venv
    fi

    # 激活虚拟环境
    source venv/bin/activate

    # 安装依赖
    echo \"安装依赖...\"
    pip install -r requirements.txt -q

    # 启动服务
    echo \"启动 FastAPI 服务...\"
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
}

# 本地启动前端
start_frontend_local() {
    echo -e \"${YELLOW}正在启动前端服务...${NC}\"

    cd frontend

    # 检查 node_modules
    if [ ! -d \"node_modules\" ]; then
        echo \"安装依赖...\"
        npm install
    fi

    # 启动开发服务器
    echo \"启动 Vue 开发服务器...\"
    npm run dev
}

# Docker 启动
start_docker() {
    echo -e \"${YELLOW}正在启动 Docker 服务...${NC}\"

    # 检查环境变量
    if [ ! -f \"backend/.env\" ]; then
        echo \"创建环境变量文件...\"
        cp backend/.env.example backend/.env
        echo -e \"${YELLOW}请编辑 backend/.env 填入您的 API Keys${NC}\"
    fi

    # 构建并启动
    docker-compose up -d --build

    echo -e \"${GREEN}服务已启动:${NC}\"
    echo \"  - 后端: http://localhost:8000\"
    echo \"  - 前端: http://localhost:5173\"
    echo \"  - API 文档: http://localhost:8000/docs\"
}

# 停止 Docker
stop_docker() {
    echo -e \"${YELLOW}停止 Docker 服务...${NC}\"
    docker-compose down
}

# 显示帮助
show_help() {
    echo \"用法: ./run.sh [命令]\"
    echo \"\"
    echo \"命令:\"
    echo \"  docker      使用 Docker 启动（推荐）\"
    echo \"  docker:build  构建 Docker 镜像\"
    echo \"  docker:stop  停止 Docker 服务\"
    echo \"  backend     本地启动后端\"
    echo \"  frontend    本地启动前端\"
    echo \"  all         本地启动前后端\"
    echo \"  help        显示帮助\"
}

# 主逻辑
case \"$1\" in
    docker)
        check_docker
        start_docker
        ;;
    docker:build)
        check_docker
        docker-compose build
        ;;
    docker:stop)
        check_docker
        stop_docker
        ;;
    backend)
        start_backend_local
        ;;
    frontend)
        start_frontend_local
        ;;
    all)
        echo \"启动后端...\"
        start_backend_local &
        echo \"启动前端...\"
        start_frontend_local &
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e \"${RED}未知命令: $1${NC}\"
        show_help
        exit 1
        ;;
esac