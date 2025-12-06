#!/usr/bin/env python3
"""
API 连接和响应格式测试脚本
"""
import os
import sys
import asyncio
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_api_connection():
    """测试 OpenAI API 连接"""
    print("\n" + "="*70)
    print("1️⃣ 测试 OpenAI API 连接")
    print("="*70)

    try:
        from openai import OpenAI

        api_key = os.getenv("OPENAI_API_KEY")
        api_base = os.getenv("OPENAI_API_BASE")

        if not api_key:
            print("❌ OPENAI_API_KEY 未配置")
            return False

        print(f"✓ API Key: {api_key[:20]}...")
        print(f"✓ API Base: {api_base}")

        client = OpenAI(
            api_key=api_key,
            base_url=api_base if api_base else "https://api.openai.com/v1"
        )

        print("\n尝试调用 API...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "说你好"}],
            max_tokens=50,
            temperature=0.5
        )

        result = response.choices[0].message.content
        print(f"✅ API 响应成功: {result}")
        return True

    except Exception as e:
        print(f"❌ API 连接失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_agent_llm():
    """测试 Agent LLM 功能"""
    print("\n" + "="*70)
    print("2️⃣ 测试 Agent LLM 功能")
    print("="*70)

    try:
        from tools.tool_manager import ToolManager
        from core.agent import MultiTaskAgent

        tool_manager = ToolManager()
        agent = MultiTaskAgent(tool_manager, use_llm=True)

        if not agent.use_llm:
            print("⚠️  LLM 未启用，仅使用规则引擎")
            return True

        print("✓ Agent 已初始化")
        print("\n尝试分类任务...")

        task_type = agent._classify_task_with_llm("北京天气怎么样")
        print(f"✅ 任务分类: {task_type}")

        print("\n尝试生成工具调用...")
        tool_calls = agent._generate_tool_calls_with_llm(
            "北京天气怎么样",
            task_type
        )
        print(f"✅ 工具调用: {tool_calls}")

        return True

    except Exception as e:
        print(f"❌ Agent 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_full_query():
    """完整查询测试"""
    print("\n" + "="*70)
    print("3️⃣ 完整查询处理测试")
    print("="*70)

    try:
        from tools.tool_manager import ToolManager
        from core.agent import MultiTaskAgent

        tool_manager = ToolManager()
        agent = MultiTaskAgent(tool_manager, use_llm=True)

        queries = [
            "北京天气如何?",
            "最新科技新闻",
            "搜索 Python 教程"
        ]

        for query in queries:
            print(f"\n📝 查询: {query}")
            result = await agent.process_query(query)
            print(f"✅ 响应: {result['response'][:100]}...")
            print(f"   类型: {result['task_type']}")
            print(f"   工具: {len(result['tool_calls'])} 个")

        return True

    except Exception as e:
        print(f"❌ 完整测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("\n" + "🔍 "*20)
    print("API 连接和响应格式诊断")
    print("🔍 "*20)

    results = []

    # 测试 1: API 连接
    results.append(await test_api_connection())

    # 测试 2: Agent LLM
    results.append(await test_agent_llm())

    # 测试 3: 完整查询
    results.append(await test_full_query())

    # 总结
    print("\n" + "="*70)
    print("📊 测试总结")
    print("="*70)

    passed = sum(results)
    total = len(results)

    print(f"\n通过: {passed}/{total}")

    if passed == total:
        print("\n✅ 所有测试通过！API 正常工作。")
        print("\n现在可以启动服务器:")
        print("  cd src && python -m uvicorn main:app --reload")
    else:
        print("\n⚠️ 部分测试失败，请查看上面的错误信息")
        print("\n建议:")
        print("1. 检查 OpenAI API Key 和 Base URL")
        print("2. 查看 API_ERROR_FIX.md 了解详细信息")
        print("3. 如需禁用 LLM，使用规则引擎")

    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
