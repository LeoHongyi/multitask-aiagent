#!/bin/bash

# 多任务AI问答助手 - SSL 证书修复和依赖安装脚本

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  🔧 多任务AI问答助手 - 依赖安装脚本（SSL 修复版）             ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# 获取当前目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "📍 项目目录: $SCRIPT_DIR"
echo ""

# 步骤 1: 升级 pip 和 certifi
echo "步骤 1️⃣ : 升级 pip 和 certifi..."
pip install --upgrade pip certifi --trusted-host pypi.org --trusted-host files.pythonhosted.org

echo ""
echo "步骤 2️⃣ : 尝试安装依赖..."
echo ""

# 尝试方案 1: 使用 trusted-host
echo "方案 1️⃣ : 使用 --trusted-host 参数..."
pip install --trusted-host pypi.org \
            --trusted-host files.pythonhosted.org \
            -r "$SCRIPT_DIR/requirements.txt"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 安装成功！"
    echo ""
    echo "下一步："
    echo "  1. cd $SCRIPT_DIR"
    echo "  2. python verify.py"
    echo ""
    exit 0
fi

# 尝试方案 2: 使用阿里云镜像
echo ""
echo "方案 1️⃣ 失败，尝试方案 2️⃣ : 使用阿里云镜像..."
pip install -i https://mirrors.aliyun.com/pypi/simple/ \
            -r "$SCRIPT_DIR/requirements.txt"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 安装成功（使用阿里云镜像）！"
    echo ""
    echo "下一步："
    echo "  1. cd $SCRIPT_DIR"
    echo "  2. python verify.py"
    echo ""
    exit 0
fi

# 尝试方案 3: 使用豆瓣镜像
echo ""
echo "方案 2️⃣ 失败，尝试方案 3️⃣ : 使用豆瓣镜像..."
pip install -i http://pypi.douban.com/simple \
            -r "$SCRIPT_DIR/requirements.txt"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 安装成功（使用豆瓣镜像）！"
    echo ""
    echo "下一步："
    echo "  1. cd $SCRIPT_DIR"
    echo "  2. python verify.py"
    echo ""
    exit 0
fi

# 所有方案都失败
echo ""
echo "❌ 所有安装方案都失败了"
echo ""
echo "请尝试以下方法之一："
echo ""
echo "方法 1️⃣ : 手动运行（选择一个国内镜像）"
echo "  pip install -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt"
echo ""
echo "方法 2️⃣ : 检查网络连接"
echo "  - 确认网络正常"
echo "  - 如在公司网络，配置代理"
echo ""
echo "方法 3️⃣ : 查看详细指南"
echo "  cat SSL_FIX_GUIDE.md"
echo ""
echo "方法 4️⃣ : 更新 Python 证书（macOS）"
echo "  /Applications/Python\\ 3.x/Install\\ Certificates.command"
echo ""

exit 1
