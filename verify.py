#!/usr/bin/env python
"""
快速验证脚本 - 检查项目是否能正常运行
"""
import asyncio
import sys
import os

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def verify_project():
    """验证项目完整性"""
    print("\n" + "="*70)
    print("🔍 多任务AI问答助手 - 快速验证")
    print("="*70)

    # 1. 检查文件结构
    print("\n1️⃣ 检查项目文件结构...")
    required_files = [
        'src/main.py',
        'src/core/agent.py',
        'src/tools/tool_manager.py',
        'src/utils/redis_manager.py',
        'src/schemas/models.py',
        '.env',
        'requirements.txt',
    ]

    for file in required_files:
        path = os.path.join(os.path.dirname(__file__), file)
        if os.path.exists(path):
            print(f"   ✓ {file}")
        else:
            print(f"   ✗ {file} 缺失")

    # 2. 检查依赖
    print("\n2️⃣ 检查依赖包...")
    try:
        from tools.tool_manager import ToolManager
        from core.agent import MultiTaskAgent
        from utils.redis_manager import RedisManager
        print("   ✓ 所有核心模块可导入")
    except Exception as e:
        print(f"   ✗ 导入失败: {e}")
        return False

    # 3. 验证工具管理器
    print("\n3️⃣ 验证 ToolManager...")
    try:
        tool_manager = ToolManager()
        tools = tool_manager.get_tool_descriptions()
        print(f"   ✓ 已加载 {len(tools)} 个工具:")
        for name, desc in tools.items():
            print(f"      • {name}: {desc}")
    except Exception as e:
        print(f"   ✗ 工具加载失败: {e}")
        return False

    # 4. 验证 Agent
    print("\n4️⃣ 验证 MultiTaskAgent...")
    try:
        agent = MultiTaskAgent(tool_manager, use_llm=False)

        # 测试规则引擎
        result = await agent.process_query("北京天气")
        print(f"   ✓ Agent 可正常运行")
        print(f"   ✓ 任务类型识别: {result['task_type']}")
        print(f"   ✓ 响应: {result['response'][:50]}...")
    except Exception as e:
        print(f"   ✗ Agent 测试失败: {e}")
        return False

    # 5. 验证 Redis 连接
    print("\n5️⃣ 检查 Redis 连接...")
    try:
        redis_manager = RedisManager()
        if redis_manager.health_check():
            print("   ✓ Redis 连接正常")
        else:
            print("   ⚠️  Redis 连接失败（可选，不影响使用）")
    except Exception as e:
        print(f"   ⚠️  Redis 检查失败: {e}")

    # 6. 验证 FastAPI
    print("\n6️⃣ 验证 FastAPI 服务器...")
    try:
        from main import app
        print("   ✓ FastAPI 应用加载成功")
        print(f"   ✓ 已定义 {len(app.routes)} 个路由")
    except Exception as e:
        print(f"   ✗ FastAPI 加载失败: {e}")
        return False

    # 7. 验证环境变量
    print("\n7️⃣ 检查 OpenAI 配置...")
    api_key = os.getenv("OPENAI_API_KEY")
    api_base = os.getenv("OPENAI_API_BASE")

    if api_key and api_base:
        print(f"   ✓ OPENAI_API_KEY: {api_key[:20]}...")
        print(f"   ✓ OPENAI_API_BASE: {api_base}")
    else:
        print("   ⚠️  未配置 OpenAI API Key（可选，支持规则引擎降级）")

    return True

async def main():
    """主函数"""
    success = await verify_project()

    print("\n" + "="*70)
    if success:
        print("✅ 项目验证完成！所有关键组件正常。")
        print("\n🚀 下一步:")
        print("   1. 启动 Redis (可选):")
        print("      redis-server &")
        print()
        print("   2. 启动 FastAPI 服务器:")
        print("      cd src && python -m uvicorn main:app --reload")
        print()
        print("   3. 访问 API 文档:")
        print("      http://localhost:8000/docs")
    else:
        print("❌ 项目验证失败，请检查错误信息。")
        sys.exit(1)

    print("="*70 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
