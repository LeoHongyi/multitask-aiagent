"""
客服中心专用工具集
"""
import json
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import uuid

from schemas.customer_service_models import (
    Customer, Ticket, Agent, TicketStatus, TicketPriority,
    CustomerLevel, ChannelType, CustomerServiceTaskType
)


class BaseCustomerServiceTool:
    """客服工具基类"""

    def __init__(self):
        self.name = self.__class__.__name__
        self.description = self.__class__.__doc__ or "客服专用工具"

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具"""
        raise NotImplementedError("子类必须实现execute方法")


class CustomerLookupTool(BaseCustomerServiceTool):
    """客户查询工具 - 查找客户信息和历史记录"""

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        查询客户信息

        Parameters:
        - phone: 手机号
        - email: 邮箱
        - customer_id: 客户ID
        - name: 姓名
        """
        try:
            phone = parameters.get("phone")
            email = parameters.get("email")
            customer_id = parameters.get("customer_id")
            name = parameters.get("name")

            # 模拟客户数据查询
            mock_customers = {
                "13800138000": {
                    "customer_id": "C001",
                    "name": "张三",
                    "phone": "13800138000",
                    "email": "zhangsan@example.com",
                    "member_level": "gold",
                    "total_orders": 15,
                    "total_complaints": 2,
                    "satisfaction_score": 4.2,
                    "tags": ["VIP客户", "电子产品爱好者"],
                    "recent_orders": [
                        {"order_id": "ORD001", "date": "2025-12-01", "amount": 2999, "status": "delivered"},
                        {"order_id": "ORD002", "date": "2025-11-28", "amount": 1599, "status": "shipped"}
                    ],
                    "last_contact": "2025-12-05"
                },
                "13900139000": {
                    "customer_id": "C002",
                    "name": "李四",
                    "phone": "13900139000",
                    "email": "lisi@example.com",
                    "member_level": "silver",
                    "total_orders": 8,
                    "total_complaints": 1,
                    "satisfaction_score": 3.8,
                    "tags": ["活跃客户"],
                    "recent_orders": [
                        {"order_id": "ORD003", "date": "2025-12-03", "amount": 899, "status": "processing"}
                    ],
                    "last_contact": "2025-12-06"
                }
            }

            # 根据查询条件查找客户
            customer_data = None
            if phone and phone in mock_customers:
                customer_data = mock_customers[phone]
            elif customer_id:
                # 根据customer_id查找
                for customer in mock_customers.values():
                    if customer["customer_id"] == customer_id:
                        customer_data = customer
                        break
            elif email:
                # 根据email查找
                for customer in mock_customers.values():
                    if customer["email"] == email:
                        customer_data = customer
                        break
            elif name:
                # 根据姓名查找
                for customer in mock_customers.values():
                    if customer["name"] == name:
                        customer_data = customer
                        break

            if not customer_data:
                return {
                    "tool": "customer_lookup",
                    "success": False,
                    "message": "未找到客户信息",
                    "suggestions": [
                        "请确认查询信息是否正确",
                        "该客户可能是新客户，需要创建客户档案"
                    ]
                }

            return {
                "tool": "customer_lookup",
                "success": True,
                "customer": customer_data,
                "message": f"找到客户信息：{customer_data['name']}（{customer_data['member_level']}会员）"
            }

        except Exception as e:
            return {
                "tool": "customer_lookup",
                "success": False,
                "error": str(e),
                "message": "客户信息查询失败"
            }


class OrderQueryTool(BaseCustomerServiceTool):
    """订单查询工具 - 查询订单详细信息"""

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        查询订单信息

        Parameters:
        - order_id: 订单号
        - customer_id: 客户ID（可选，用于验证权限）
        """
        try:
            order_id = parameters.get("order_id")
            customer_id = parameters.get("customer_id")

            if not order_id:
                return {
                    "tool": "order_query",
                    "success": False,
                    "error": "缺少订单号",
                    "message": "请提供订单号"
                }

            # 模拟订单数据
            mock_orders = {
                "ORD001": {
                    "order_id": "ORD001",
                    "customer_id": "C001",
                    "customer_name": "张三",
                    "order_date": "2025-12-01 14:30:00",
                    "total_amount": 2999.00,
                    "status": "delivered",
                    "payment_status": "paid",
                    "shipping_address": "北京市朝阳区某某街道123号",
                    "logistics_company": "顺丰快递",
                    "tracking_number": "SF1234567890",
                    "products": [
                        {"name": "iPhone 15 Pro", "quantity": 1, "price": 2999.00, "sku": "IP15P001"}
                    ],
                    "estimated_delivery": "2025-12-05",
                    "actual_delivery": "2025-12-04 16:20:00",
                    "notes": "客户要求尽快发货"
                },
                "ORD002": {
                    "order_id": "ORD002",
                    "customer_id": "C001",
                    "customer_name": "张三",
                    "order_date": "2025-11-28 10:15:00",
                    "total_amount": 1599.00,
                    "status": "shipped",
                    "payment_status": "paid",
                    "shipping_address": "北京市朝阳区某某街道123号",
                    "logistics_company": "圆通快递",
                    "tracking_number": "YT9876543210",
                    "products": [
                        {"name": "AirPods Pro", "quantity": 1, "price": 1599.00, "sku": "APP002"}
                    ],
                    "estimated_delivery": "2025-12-07",
                    "actual_delivery": None,
                    "notes": "备注：礼品包装"
                },
                "ORD003": {
                    "order_id": "ORD003",
                    "customer_id": "C002",
                    "customer_name": "李四",
                    "order_date": "2025-12-03 16:45:00",
                    "total_amount": 899.00,
                    "status": "processing",
                    "payment_status": "paid",
                    "shipping_address": "上海市浦东新区某某路456号",
                    "logistics_company": None,
                    "tracking_number": None,
                    "products": [
                        {"name": "小米手环8", "quantity": 2, "price": 449.50, "sku": "MB008"}
                    ],
                    "estimated_delivery": "2025-12-10",
                    "actual_delivery": None,
                    "notes": "客户是第一次购买"
                }
            }

            order_data = mock_orders.get(order_id)

            if not order_data:
                return {
                    "tool": "order_query",
                    "success": False,
                    "message": f"订单号 {order_id} 未找到",
                    "suggestions": [
                        "请检查订单号是否正确",
                        "该订单可能属于其他客户"
                    ]
                }

            # 如果提供了客户ID，验证权限
            if customer_id and order_data["customer_id"] != customer_id:
                return {
                    "tool": "order_query",
                    "success": False,
                    "message": "无权查询该订单信息",
                    "suggestions": [
                        "请确认客户身份",
                        "联系主管获取权限"
                    ]
                }

            # 添加状态说明
            status_descriptions = {
                "pending": "待处理",
                "processing": "处理中",
                "shipped": "已发货",
                "delivered": "已送达",
                "cancelled": "已取消"
            }

            order_data["status_description"] = status_descriptions.get(order_data["status"], "未知状态")

            return {
                "tool": "order_query",
                "success": True,
                "order": order_data,
                "message": f"订单 {order_id} 查询成功"
            }

        except Exception as e:
            return {
                "tool": "order_query",
                "success": False,
                "error": str(e),
                "message": "订单查询失败"
            }


class LogisticsTrackingTool(BaseCustomerServiceTool):
    """物流追踪工具 - 查询物流信息"""

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        查询物流信息

        Parameters:
        - tracking_number: 快递单号
        - logistics_company: 物流公司（可选）
        - order_id: 订单号（可选）
        """
        try:
            tracking_number = parameters.get("tracking_number")
            logistics_company = parameters.get("logistics_company")
            order_id = parameters.get("order_id")

            if not tracking_number and not order_id:
                return {
                    "tool": "logistics_tracking",
                    "success": False,
                    "error": "请提供快递单号或订单号",
                    "message": "需要tracking_number或order_id参数"
                }

            # 模拟物流数据
            mock_logistics = {
                "SF1234567890": {
                    "tracking_number": "SF1234567890",
                    "logistics_company": "顺丰快递",
                    "order_id": "ORD001",
                    "status": "delivered",
                    "current_location": "北京市朝阳区某某街道",
                    "estimated_delivery": "2025-12-05",
                    "tracking_history": [
                        {"time": "2025-12-01 18:30", "location": "北京分拨中心", "status": "已揽收"},
                        {"time": "2025-12-02 02:15", "location": "北京转运中心", "status": "运输中"},
                        {"time": "2025-12-03 08:45", "location": "北京朝阳营业点", "status": "派送中"},
                        {"time": "2025-12-04 16:20", "location": "已签收", "status": "已送达"}
                    ]
                },
                "YT9876543210": {
                    "tracking_number": "YT9876543210",
                    "logistics_company": "圆通快递",
                    "order_id": "ORD002",
                    "status": "in_transit",
                    "current_location": "上海分拨中心",
                    "estimated_delivery": "2025-12-07",
                    "tracking_history": [
                        {"time": "2025-12-05 14:20", "location": "上海分拨中心", "status": "已揽收"},
                        {"time": "2025-12-06 03:30", "location": "上海转运中心", "status": "运输中"}
                    ]
                }
            }

            logistics_data = None

            # 根据快递单号查询
            if tracking_number:
                logistics_data = mock_logistics.get(tracking_number)

            # 根据订单号查询
            elif order_id:
                for logistics in mock_logistics.values():
                    if logistics["order_id"] == order_id:
                        logistics_data = logistics
                        break

            if not logistics_data:
                return {
                    "tool": "logistics_tracking",
                    "success": False,
                    "message": "未找到物流信息",
                    "suggestions": [
                        "请确认快递单号是否正确",
                        "物流信息可能还未更新",
                        "联系物流公司客服"
                    ]
                }

            # 添加状态说明
            status_descriptions = {
                "picked_up": "已揽收",
                "in_transit": "运输中",
                "out_for_delivery": "派送中",
                "delivered": "已送达",
                "exception": "异常"
            }

            logistics_data["status_description"] = status_descriptions.get(
                logistics_data["status"], "未知状态"
            )

            return {
                "tool": "logistics_tracking",
                "success": True,
                "logistics": logistics_data,
                "message": f"物流信息查询成功：{logistics_data['logistics_company']}"
            }

        except Exception as e:
            return {
                "tool": "logistics_tracking",
                "success": False,
                "error": str(e),
                "message": "物流信息查询失败"
            }


class RefundProcessTool(BaseCustomerServiceTool):
    """退款处理工具 - 处理退款申请"""

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理退款申请

        Parameters:
        - order_id: 订单号
        - customer_id: 客户ID
        - refund_amount: 退款金额
        - refund_reason: 退款原因
        - refund_type: 退款类型 (full, partial)
        """
        try:
            order_id = parameters.get("order_id")
            customer_id = parameters.get("customer_id")
            refund_amount = parameters.get("refund_amount")
            refund_reason = parameters.get("refund_reason")
            refund_type = parameters.get("refund_type", "full")

            if not all([order_id, customer_id, refund_reason]):
                return {
                    "tool": "refund_process",
                    "success": False,
                    "error": "缺少必要参数",
                    "message": "需要订单号、客户ID和退款原因"
                }

            # 模拟退款处理
            refund_id = f"REF{datetime.now().strftime('%Y%m%d%H%M%S')}"

            # 根据退款类型计算金额
            if refund_type == "full":
                # 全额退款，这里假设订单金额
                mock_order_amounts = {"ORD001": 2999.00, "ORD002": 1599.00, "ORD003": 899.00}
                calculated_amount = mock_order_amounts.get(order_id, 0.0)
            else:
                calculated_amount = float(refund_amount) if refund_amount else 0.0

            # 模拟处理时间
            processing_time = "3-5个工作日" if calculated_amount < 1000 else "5-7个工作日"

            # 检查退款政策
            refund_policies = {
                "质量问题": "全额退款，运费由商家承担",
                "尺寸不合适": "7天内无理由退货，运费由客户承担",
                "个人原因": "7天内无理由退货，运费由客户承担",
                "商品损坏": "全额退款，运费由商家承担"
            }

            policy = refund_policies.get(refund_reason, "按标准退货政策处理")

            return {
                "tool": "refund_process",
                "success": True,
                "refund_id": refund_id,
                "order_id": order_id,
                "refund_amount": calculated_amount,
                "refund_type": refund_type,
                "processing_time": processing_time,
                "policy": policy,
                "status": "processing",
                "message": f"退款申请已提交，退款ID：{refund_id}"
            }

        except Exception as e:
            return {
                "tool": "refund_process",
                "success": False,
                "error": str(e),
                "message": "退款申请处理失败"
            }


class TicketCreateTool(BaseCustomerServiceTool):
    """工单创建工具 - 创建客服工单"""

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建客服工单

        Parameters:
        - customer_id: 客户ID
        - title: 工单标题
        - description: 问题描述
        - category: 工单分类
        - priority: 优先级
        - channel: 接入渠道
        """
        try:
            customer_id = parameters.get("customer_id")
            title = parameters.get("title")
            description = parameters.get("description")
            category = parameters.get("category")
            priority = parameters.get("priority", "medium")
            channel = parameters.get("channel", "web")

            if not all([customer_id, title, description, category]):
                return {
                    "tool": "ticket_create",
                    "success": False,
                    "error": "缺少必要参数",
                    "message": "需要客户ID、标题、描述和分类"
                }

            # 生成工单ID
            ticket_id = f"TK{datetime.now().strftime('%Y%m%d%H%M%S')}"

            # 估算解决时间
            resolution_times = {
                "urgent": "1小时内",
                "high": "4小时内",
                "medium": "24小时内",
                "low": "48小时内"
            }

            estimated_resolution = resolution_times.get(priority, "24小时内")

            # 模拟自动分配客服
            agent_assignment = self._auto_assign_agent(category, priority)

            return {
                "tool": "ticket_create",
                "success": True,
                "ticket_id": ticket_id,
                "customer_id": customer_id,
                "title": title,
                "category": category,
                "priority": priority,
                "channel": channel,
                "status": "pending",
                "assigned_agent": agent_assignment,
                "estimated_resolution": estimated_resolution,
                "created_at": datetime.now().isoformat(),
                "message": f"工单创建成功，工单号：{ticket_id}"
            }

        except Exception as e:
            return {
                "tool": "ticket_create",
                "success": False,
                "error": str(e),
                "message": "工单创建失败"
            }

    def _auto_assign_agent(self, category: str, priority: str) -> Optional[str]:
        """自动分配客服专员"""
        # 模拟客服专员技能匹配
        agent_skills = {
            "order_issue": ["agent001", "agent003"],
            "logistics_issue": ["agent002"],
            "refund_return": ["agent001", "agent004"],
            "tech_support": ["agent003"],
            "complaint": ["agent004", "agent005"]
        }

        available_agents = agent_skills.get(category, ["agent001"])
        return available_agents[0] if available_agents else None


class KnowledgeSearchTool(BaseCustomerServiceTool):
    """知识库搜索工具 - 搜索解决方案"""

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        搜索知识库

        Parameters:
        - query: 搜索关键词
        - category: 问题分类
        - limit: 返回结果数量限制
        """
        try:
            query = parameters.get("query", "")
            category = parameters.get("category")
            limit = parameters.get("limit", 5)

            # 模拟知识库数据
            mock_knowledge = [
                {
                    "kb_id": "KB001",
                    "title": "订单修改流程",
                    "category": "order_issue",
                    "content": "客户可以在订单状态为'待处理'时修改订单信息...",
                    "keywords": ["订单修改", "地址修改", "商品修改"],
                    "usage_count": 156,
                    "helpful_count": 142
                },
                {
                    "kb_id": "KB002",
                    "title": "退换货政策说明",
                    "category": "refund_return",
                    "content": "7天内无理由退货，商品需保持原包装完好...",
                    "keywords": ["退换货", "7天无理由", "包装完好"],
                    "usage_count": 203,
                    "helpful_count": 189
                },
                {
                    "kb_id": "KB003",
                    "title": "物流时效查询",
                    "category": "logistics_issue",
                    "content": "不同地区的物流时效不同，一般一线城市2-3天...",
                    "keywords": ["物流时效", "配送时间", "地区差异"],
                    "usage_count": 98,
                    "helpful_count": 85
                },
                {
                    "kb_id": "KB004",
                    "title": "商品质量问题处理",
                    "category": "complaint",
                    "content": "收到商品后发现质量问题，请第一时间拍照留证...",
                    "keywords": ["质量问题", "拍照留证", "换货流程"],
                    "usage_count": 67,
                    "helpful_count": 61
                }
            ]

            # 简单的关键词匹配搜索
            results = []
            for item in mock_knowledge:
                # 分类过滤
                if category and item["category"] != category:
                    continue

                # 关键词匹配
                if query and query.lower() in item["title"].lower():
                    results.append(item)
                elif query and any(query.lower() in keyword.lower() for keyword in item["keywords"]):
                    results.append(item)
                elif not query:  # 如果没有查询词，返回分类下的所有结果
                    results.append(item)

            # 按使用次数排序
            results.sort(key=lambda x: x["usage_count"], reverse=True)

            return {
                "tool": "knowledge_search",
                "success": True,
                "query": query,
                "category": category,
                "results": results[:limit],
                "total_found": len(results),
                "message": f"找到 {len(results)} 个相关知识条目"
            }

        except Exception as e:
            return {
                "tool": "knowledge_search",
                "success": False,
                "error": str(e),
                "message": "知识库搜索失败"
            }


# 客服工具注册表
CUSTOMER_SERVICE_TOOLS = {
    "customer_lookup": CustomerLookupTool(),
    "order_query": OrderQueryTool(),
    "logistics_tracking": LogisticsTrackingTool(),
    "refund_process": RefundProcessTool(),
    "ticket_create": TicketCreateTool(),
    "knowledge_search": KnowledgeSearchTool(),
}


async def execute_customer_service_tool(tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    执行客服工具

    Args:
        tool_name: 工具名称
        parameters: 工具参数

    Returns:
        工具执行结果
    """
    tool = CUSTOMER_SERVICE_TOOLS.get(tool_name)
    if not tool:
        return {
            "tool": tool_name,
            "success": False,
            "error": f"工具 {tool_name} 不存在",
            "message": "无效的工具名称"
        }

    try:
        result = await tool.execute(parameters)
        result["timestamp"] = datetime.now().isoformat()
        return result
    except Exception as e:
        return {
            "tool": tool_name,
            "success": False,
            "error": str(e),
            "message": f"工具 {tool_name} 执行失败",
            "timestamp": datetime.now().isoformat()
        }