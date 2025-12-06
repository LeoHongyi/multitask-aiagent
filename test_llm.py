"""
LLM 集成测试脚本 - 验证 OpenAI API 连接
"""
import asyncio
import sys
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from tools.tool_manager import ToolManager
from core.agent import MultiTaskAgent


async def test_openai_integration():
    """测试 OpenAI 集成"""
    print("\n" + "="*60)
    print("OpenAI LLM 集成测试")
    print("="*60)

    tool_manager = ToolManager()
    agent = MultiTaskAgent(tool_manager, use_llm=True)

    print(f"\n✅ LLM 已启用: {agent.use_llm}")

    if not agent.use_llm:
        print("⚠️  LLM 未启用，请检查 OpenAI 凭证配置")
        return

    test_queries = [
        "北京今天天气怎么样?",
        "最近有哪些科技新闻?",
        "搜索一下Python编程",
        "请用中文详细介绍一下人工智能"
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n{'─'*60}")
        print(f"📝 查询 {i}: {query}")
        print(f"{'─'*60}")

        try:
            result = await agent.process_query(query)

            print(f"✅ 任务类型: {result['task_type']}")
            print(f"🤖 LLM 驱动: {result['llm_used']}")
            print(f"📢 回答:\n{result['response']}")

            if result['tool_calls']:
                print(f"\n🔧 工具调用数: {len(result['tool_calls'])}")
                for tool_call in result['tool_calls']:
                    print(f"   - {tool_call.tool_name}: {tool_call.parameters}")

        except Exception as e:
            print(f"❌ 错误: {str(e)}")


async def test_fallback_to_rules():
    """测试降级到规则引擎"""
    print("\n" + "="*60)
    print("规则引擎降级测试（禁用 LLM）")
    print("="*60)

    tool_manager = ToolManager()
    agent = MultiTaskAgent(tool_manager, use_llm=False)

    print(f"\n✅ LLM 已禁用: {not agent.use_llm}")

    test_query = "北京天气"
    print(f"\n📝 查询: {test_query}")

    result = await agent.process_query(test_query)
    print(f"✅ 任务类型: {result['task_type']}")
    print(f"📢 回答:\n{result['response']}")


async def main():
    """主测试函数"""
    print("\n" + "🚀 "*20)
    print("多任务AI问答助手 - LLM 集成测试")
    print("🚀 "*20)

    # 检查环境变量
    api_key = os.getenv("OPENAI_API_KEY")
    api_base = os.getenv("OPENAI_API_BASE")

    if api_key and api_base:
        print(f"\n✅ 检测到 OpenAI 凭证")
        print(f"   API Base: {api_base}")
        print(f"   API Key: {api_key[:20]}...")
    else:
        print(f"\n⚠️  未检测到 OpenAI 凭证")
        print(f"   请在 .env 文件中设置 OPENAI_API_KEY 和 OPENAI_API_BASE")

    await test_openai_integration()
    await test_fallback_to_rules()

    print("\n" + "✅ "*20)
    print("LLM 集成测试完成!")
    print("✅ "*20 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
