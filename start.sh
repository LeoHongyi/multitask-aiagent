#!/bin/bash

# 多任务AI问答助手 - 一键启动脚本

echo "🚀 多任务AI问答助手 - 启动脚本"
echo "=================================="

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未安装 Python3"
    exit 1
fi

echo "✅ Python3 已安装"

# 检查 Redis
if ! command -v redis-server &> /dev/null; then
    echo "⚠️  未安装 Redis，建议安装以支持会话存储"
    echo "   macOS: brew install redis"
    echo "   Docker: docker run -d -p 6379:6379 redis:latest"
fi

# 安装依赖
echo ""
echo "📦 安装依赖..."
pip install -q -r requirements.txt

# 检查 .env 文件
if [ ! -f .env ]; then
    echo "⚠️  未找到 .env 文件，使用默认配置"
else
    echo "✅ 加载 .env 配置"
fi

# 启动 Redis（可选）
echo ""
echo "🔧 Redis 状态检查..."
if command -v redis-server &> /dev/null; then
    if ! redis-cli ping &> /dev/null; then
        echo "启动 Redis..."
        redis-server --daemonize yes
        sleep 1
        if redis-cli ping &> /dev/null; then
            echo "✅ Redis 已启动"
        else
            echo "⚠️  Redis 启动失败，将在无会话存储的情况下运行"
        fi
    else
        echo "✅ Redis 已运行"
    fi
fi

# 启动 FastAPI 服务器
echo ""
echo "🌐 启动 FastAPI 服务器..."
cd src
echo ""
echo "📍 服务器地址: http://localhost:8000"
echo "📖 API 文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止服务器"
echo ""

python -m uvicorn main:app --reload --port 8000 --host 0.0.0.0
