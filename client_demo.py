"""
API 客户端测试 - 演示 FastAPI 端点
"""
import asyncio
import aiohttp
import json
from typing import Optional

API_BASE = "http://localhost:8000"


class MultiTaskAgentClient:
    """多任务问答助手客户端"""

    def __init__(self, base_url: str = API_BASE):
        self.base_url = base_url
        self.session_id = None

    async def health_check(self) -> dict:
        """健康检查"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/health") as resp:
                return await resp.json()

    async def start_session(self) -> str:
        """创建新会话"""
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.base_url}/api/session/start") as resp:
                data = await resp.json()
                self.session_id = data.get("session_id")
                return self.session_id

    async def chat(self, query: str, session_id: Optional[str] = None) -> dict:
        """发送聊天请求"""
        payload = {
            "query": query,
            "session_id": session_id or self.session_id
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/chat",
                json=payload
            ) as resp:
                return await resp.json()

    async def get_session(self, session_id: str) -> dict:
        """获取会话历史"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/api/session/{session_id}") as resp:
                return await resp.json()

    async def delete_session(self, session_id: str) -> dict:
        """删除会话"""
        async with aiohttp.ClientSession() as session:
            async with session.delete(f"{self.base_url}/api/session/{session_id}") as resp:
                return await resp.json()

    async def get_tools(self) -> dict:
        """获取可用工具列表"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/api/tools") as resp:
                return await resp.json()


async def main():
    """演示客户端用法"""
    print("\n" + "="*70)
    print("多任务AI问答助手 - API 客户端演示")
    print("="*70)

    client = MultiTaskAgentClient()

    # 1. 健康检查
    print("\n1️⃣  健康检查...")
    try:
        health = await client.health_check()
        print(f"✅ 服务状态: {health['status']}")
        print(f"   Redis: {'✅' if health['redis'] else '❌'}")
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        print("   请先运行: cd src && python -m uvicorn main:app --reload")
        return

    # 2. 获取可用工具
    print("\n2️⃣  获取可用工具...")
    tools = await client.get_tools()
    print(f"✅ 可用工具:")
    for tool_name, description in tools.get("tools", {}).items():
        print(f"   - {tool_name}: {description}")

    # 3. 创建会话
    print("\n3️⃣  创建新会话...")
    session_id = await client.start_session()
    print(f"✅ 会话 ID: {session_id}")

    # 4. 多轮对话测试
    test_queries = [
        "北京今天天气怎么样?",
        "最近有什么科技新闻吗?",
        "搜索一下Python编程最佳实践",
    ]

    print("\n4️⃣  多轮对话测试...")
    for i, query in enumerate(test_queries, 1):
        print(f"\n   📝 问题 {i}: {query}")

        response = await client.chat(query)

        print(f"   ✅ 任务类型: {response['task_type']}")
        print(f"   📢 回答:\n      {response['response']}")

        if response.get('tool_calls'):
            print(f"   🔧 工具调用数: {len(response['tool_calls'])}")

    # 5. 检索会话历史
    print(f"\n5️⃣  检索会话历史...")
    session_data = await client.get_session(session_id)
    print(f"✅ 会话消息数: {len(session_data['messages'])}")
    print(f"   创建时间: {session_data['created_at']}")

    # 6. 删除会话
    print(f"\n6️⃣  删除会话...")
    delete_result = await client.delete_session(session_id)
    print(f"✅ {delete_result['message']}")

    print("\n" + "="*70)
    print("✅ 所有 API 演示完成!")
    print("="*70 + "\n")


if __name__ == "__main__":
    print("""
使用说明：
1. 确保 Redis 正在运行
2. 启动 FastAPI 服务器:
   cd src
   python -m uvicorn main:app --reload

3. 在新的终端运行此脚本:
   python client_demo.py
    """)

    asyncio.run(main())
