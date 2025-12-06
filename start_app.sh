#!/bin/bash

echo "🚀 AI Assistant 启动脚本"
echo "========================"

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
SRC_DIR="$SCRIPT_DIR/src"

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "❌ 未找到 Node.js，请先安装"
    exit 1
fi

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python3，请先安装"
    exit 1
fi

# 构建前端
echo ""
echo "📦 构建前端..."
cd "$FRONTEND_DIR"

if [ ! -d "node_modules" ]; then
    echo "   安装依赖..."
    npm install
fi

echo "   构建生产版本..."
npm run build

if [ ! -d "dist" ]; then
    echo "❌ 前端构建失败"
    exit 1
fi

echo "✅ 前端构建完成"

# 启动后端
echo ""
echo "🌐 启动服务器..."
cd "$SRC_DIR"

python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

