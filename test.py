"""
测试脚本 - 验证多任务问答助手功能
"""
import asyncio
import sys
import os

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from tools.tool_manager import ToolManager
from core.agent import MultiTaskAgent
from utils.redis_manager import RedisManager


async def test_basic_agent():
    """测试基础 Agent 功能"""
    print("\n" + "="*60)
    print("测试基础 Agent 功能")
    print("="*60)

    tool_manager = ToolManager()
    agent = MultiTaskAgent(tool_manager)

    test_queries = [
        "北京今天天气怎么样?",
        "最近有哪些科技新闻?",
        "搜索一下Python编程",
        "你好，请问你是谁?"
    ]

    for query in test_queries:
        print(f"\n📝 用户: {query}")
        result = await agent.process_query(query)
        print(f"✅ 类型: {result['task_type']}")
        print(f"📢 回答: {result['response']}")
        print(f"🔧 工具调用: {len(result['tool_calls'])} 个")


async def test_parallel_tools():
    """测试并行工具执行"""
    print("\n" + "="*60)
    print("测试并行工具执行")
    print("="*60)

    tool_manager = ToolManager()

    tool_requests = [
        {"tool": "weather", "params": {"city": "北京"}},
        {"tool": "weather", "params": {"city": "上海"}},
        {"tool": "news", "params": {"category": "tech", "limit": 2}},
    ]

    print(f"\n🚀 执行 {len(tool_requests)} 个任务...")
    import time
    start = time.time()

    results = await tool_manager.execute_tools_parallel(tool_requests)

    elapsed = time.time() - start

    for i, result in enumerate(results, 1):
        print(f"\n✅ 任务 {i}: {result.get('tool', 'unknown')}")
        if "error" not in result:
            print(f"   结果: {list(result.keys())}")

    print(f"\n⏱️  总耗时: {elapsed:.2f} 秒")


async def test_session_management():
    """测试会话管理"""
    print("\n" + "="*60)
    print("测试会话管理（需要 Redis）")
    print("="*60)

    try:
        redis_mgr = RedisManager()

        if not redis_mgr.health_check():
            print("⚠️  Redis 连接失败，跳过会话测试")
            return

        # 创建会话
        session_id = redis_mgr.create_session()
        print(f"\n✅ 创建会话: {session_id}")

        # 保存消息
        session = redis_mgr.get_session(session_id)
        if session:
            from schemas.models import Message
            session.messages.append(Message(role="user", content="你好"))
            session.messages.append(Message(role="assistant", content="你好，有什么我可以帮助的吗？"))
            redis_mgr.save_session(session)
            print(f"✅ 保存消息: {len(session.messages)} 条")

        # 检索会话
        retrieved_session = redis_mgr.get_session(session_id)
        print(f"✅ 检索会话: {len(retrieved_session.messages)} 条消息")

        # 清空会话
        redis_mgr.delete_session(session_id)
        print(f"✅ 删除会话")

    except Exception as e:
        print(f"❌ 会话测试失败: {e}")


async def test_caching():
    """测试缓存功能"""
    print("\n" + "="*60)
    print("测试缓存功能（需要 Redis）")
    print("="*60)

    try:
        redis_mgr = RedisManager()

        if not redis_mgr.health_check():
            print("⚠️  Redis 连接失败，跳过缓存测试")
            return

        # 缓存数据
        redis_mgr.cache_result("test_key", "test_value", ttl=10)
        print("✅ 缓存数据")

        # 检索缓存
        value = redis_mgr.get_cache("test_key")
        print(f"✅ 检索缓存: {value}")

        # 清空缓存
        redis_mgr.clear_cache()
        print("✅ 清空缓存")

    except Exception as e:
        print(f"❌ 缓存测试失败: {e}")


async def main():
    """主测试函数"""
    print("\n" + "🚀 "*20)
    print("多任务AI问答助手 - 测试套件")
    print("🚀 "*20)

    await test_basic_agent()
    await test_parallel_tools()
    await test_session_management()
    await test_caching()

    print("\n" + "✅ "*20)
    print("所有测试完成!")
    print("✅ "*20 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
