#!/bin/bash

# 最直接的解决方案 - 禁用 SSL 验证安装依赖

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║           🚀 直接安装依赖（禁用 SSL 验证）                      ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

echo "⚠️  注意: 这个方法禁用 SSL 验证，仅用于开发环境！"
echo ""

# 方案 1: 使用 HTTP (豆瓣镜像)
echo "方案 1️⃣ : 尝试使用 HTTP 镜像..."
pip install -i http://pypi.douban.com/simple -r requirements.txt && {
    echo ""
    echo "✅ 安装成功！"
    exit 0
}

# 方案 2: 禁用 SSL + HTTPS (阿里云)
echo ""
echo "方案 2️⃣ : 尝试禁用 SSL 验证..."
pip install -i https://mirrors.aliyun.com/pypi/simple/ \
    --cert /dev/null \
    -r requirements.txt && {
    echo ""
    echo "✅ 安装成功！"
    exit 0
}

# 方案 3: 使用 no-verify
echo ""
echo "方案 3️⃣ : 尝试 no-verify..."
pip install \
    --index-url https://mirrors.aliyun.com/pypi/simple/ \
    --trusted-host mirrors.aliyun.com \
    -r requirements.txt && {
    echo ""
    echo "✅ 安装成功！"
    exit 0
}

echo ""
echo "❌ 所有方案都失败了"
echo ""
echo "请手动运行以下命令之一:"
echo ""
echo "1️⃣ 最简单（HTTP）:"
echo "   pip install -i http://pypi.douban.com/simple -r requirements.txt"
echo ""
echo "2️⃣ 禁用 SSL:"
echo "   pip install -i https://mirrors.aliyun.com/pypi/simple/ --cert /dev/null -r requirements.txt"
echo ""
echo "3️⃣ 更新证书后重试:"
echo "   pip install --upgrade certifi"
echo "   pip install -r requirements.txt"
echo ""

exit 1
