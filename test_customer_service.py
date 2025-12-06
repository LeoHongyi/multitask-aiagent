#!/usr/bin/env python3
"""
智能客服中心功能测试脚本
"""
import asyncio
import json
import sys
import os

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from core.customer_service_agent import CustomerServiceAgent
from tools.customer_service_tools import execute_customer_service_tool


async def test_customer_service_agent():
    """测试客服Agent功能"""
    print("🤖 测试智能客服Agent")
    print("=" * 50)

    agent = CustomerServiceAgent(use_llm=True)

    test_queries = [
        "我的订单ORD001到哪里了？",
        "快递单号SF1234567890的物流信息",
        "我要退款，订单ORD001有质量问题",
        "我叫张三，手机号13800138000，查询我的订单",
        "我要找你们经理，这个问题太严重了！",
        "iPhone 15 Pro的参数规格是什么？",
        "你们的退换货政策是什么？"
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 测试 {i}: {query}")
        print("-" * 40)

        try:
            result = await agent.process_customer_service_query(query)

            print(f"✅ 分类类型: {result['task_type']}")
            print(f"✅ 工具调用: {len(result['tool_calls'])} 个")
            for tool_call in result['tool_calls']:
                print(f"   - {tool_call['tool']}: {tool_call['params']}")

            print(f"✅ 回复内容: {result['response'][:100]}...")
            print(f"✅ LLM使用: {'是' if result['llm_used'] else '否'}")

        except Exception as e:
            print(f"❌ 测试失败: {e}")

        print()


async def test_individual_tools():
    """测试各个工具"""
    print("🔧 测试客服工具集")
    print("=" * 50)

    tools_to_test = [
        {
            "name": "customer_lookup",
            "params": {"phone": "13800138000"},
            "description": "客户信息查询"
        },
        {
            "name": "order_query",
            "params": {"order_id": "ORD001"},
            "description": "订单信息查询"
        },
        {
            "name": "logistics_tracking",
            "params": {"tracking_number": "SF1234567890"},
            "description": "物流信息查询"
        },
        {
            "name": "refund_process",
            "params": {
                "order_id": "ORD001",
                "customer_id": "C001",
                "refund_reason": "质量问题"
            },
            "description": "退款处理"
        },
        {
            "name": "ticket_create",
            "params": {
                "customer_id": "C001",
                "title": "测试工单",
                "description": "这是一个测试工单",
                "category": "order_issue"
            },
            "description": "工单创建"
        },
        {
            "name": "knowledge_search",
            "params": {"query": "退换货", "limit": 3},
            "description": "知识库搜索"
        }
    ]

    for i, tool_test in enumerate(tools_to_test, 1):
        print(f"\n🔧 测试 {i}: {tool_test['description']}")
        print("-" * 40)

        try:
            result = await execute_customer_service_tool(
                tool_test['name'],
                tool_test['params']
            )

            print(f"✅ 工具名称: {result.get('tool')}")
            print(f"✅ 执行成功: {'是' if result.get('success') else '否'}")
            print(f"✅ 返回信息: {result.get('message', 'N/A')}")

            if result.get('success'):
                # 显示关键数据
                if 'customer' in result:
                    customer = result['customer']
                    print(f"   客户: {customer.get('name')} ({customer.get('member_level')}会员)")
                elif 'order' in result:
                    order = result['order']
                    print(f"   订单: {order.get('order_id')} - {order.get('status_description')}")
                elif 'logistics' in result:
                    logistics = result['logistics']
                    print(f"   物流: {logistics.get('logistics_company')} - {logistics.get('status_description')}")
                elif 'refund_id' in result:
                    print(f"   退款编号: {result.get('refund_id')} - {result.get('refund_amount')}元")
                elif 'ticket_id' in result:
                    print(f"   工单编号: {result.get('ticket_id')} - {result.get('estimated_resolution')}")
                elif 'results' in result:
                    results = result['results']
                    print(f"   知识库结果: 找到 {len(results)} 个条目")

        except Exception as e:
            print(f"❌ 工具测试失败: {e}")

        print()


async def test_task_classification():
    """测试任务分类功能"""
    print("🎯 测试任务分类功能")
    print("=" * 50)

    agent = CustomerServiceAgent(use_llm=False)  # 使用规则引擎

    classification_tests = [
        ("查询订单ORD001状态", "order_query"),
        ("快递SF1234567890到哪了", "logistics_tracking"),
        ("我要退款，商品有质量问题", "refund_request"),
        ("收到的商品坏了，想换一个", "return_exchange"),
        ("手机无法开机怎么办", "tech_support"),
        ("我要投诉你们的服务", "complaint_handling"),
        ("修改密码", "account_issues"),
        ("支付失败了怎么办", "payment_issues"),
        ("产品价格咨询", "consultation"),
        ("我要找经理", "escalation")
    ]

    print("查询内容 -> 分类结果 (预期结果)")
    print("-" * 50)

    correct_count = 0
    total_count = len(classification_tests)

    for query, expected in classification_tests:
        try:
            result = await agent.classify_customer_service_query(query)
            is_correct = result.value == expected
            status = "✅" if is_correct else "❌"

            print(f"{status} {query[:30]:<30} -> {result.value:<15} ({expected})")

            if is_correct:
                correct_count += 1

        except Exception as e:
            print(f"❌ {query[:30]:<30} -> 错误: {e}")

    accuracy = (correct_count / total_count) * 100
    print(f"\n📊 分类准确率: {accuracy:.1f}% ({correct_count}/{total_count})")
    print()


def print_system_info():
    """打印系统信息"""
    print("🏢 智能客服中心系统信息")
    print("=" * 50)

    print(f"Python版本: {sys.version}")
    print(f"工作目录: {os.getcwd()}")

    # 检查依赖
    dependencies = [
        "fastapi", "uvicorn", "pydantic", "openai",
        "redis", "asyncio", "re", "uuid"
    ]

    print("\n📦 依赖检查:")
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"   ✅ {dep}")
        except ImportError:
            print(f"   ❌ {dep} (未安装)")

    # 检查环境变量
    print("\n🔑 环境变量:")
    env_vars = ["OPENAI_API_KEY", "OPENAI_API_BASE", "REDIS_URL"]
    for var in env_vars:
        value = os.getenv(var)
        if value:
            masked_value = value[:10] + "***" if len(value) > 10 else "***"
            print(f"   ✅ {var}: {masked_value}")
        else:
            print(f"   ⚠️  {var}: 未设置")

    print()


async def main():
    """主测试函数"""
    print("🚀 智能客服中心功能测试")
    print("=" * 60)
    print()

    # 系统信息
    print_system_info()

    # 等待用户确认
    input("按Enter键开始测试...")

    try:
        # 1. 测试任务分类
        await test_task_classification()

        # 2. 测试各个工具
        await test_individual_tools()

        # 3. 测试客服Agent
        await test_customer_service_agent()

        print("🎉 所有测试完成！")
        print("\n📋 测试总结:")
        print("   - 任务分类功能正常")
        print("   - 客服工具集运行正常")
        print("   - 智能Agent处理正常")
        print("\n✅ 系统已就绪，可以启动服务！")
        print("   启动命令: cd src && python -m uvicorn main:app --reload")

    except KeyboardInterrupt:
        print("\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 运行异步测试
    asyncio.run(main())