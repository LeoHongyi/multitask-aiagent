"""
多Agent协同客服系统 - Agent定义
"""
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
import re
from datetime import datetime

import sys
sys.path.append('..')

from schemas.agent_models import AgentRole, TaskType, AgentResponse, TaskStatus
from data.mock_database import MockDatabase


class BaseAgent(ABC):
    """Agent基类"""

    def __init__(self, role: AgentRole):
        self.role = role
        self.db = MockDatabase()

    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """处理任务"""
        pass


class RouterAgent(BaseAgent):
    """路由Agent - 负责任务分类和分发"""

    def __init__(self):
        super().__init__(AgentRole.ROUTER)

        # 关键词映射
        self.keywords = {
            TaskType.ORDER_QUERY: ["订单", "查询", "物流", "快递", "到哪了", "发货"],
            TaskType.ORDER_STATUS: ["状态", "进度", "什么时候到"],
            TaskType.REFUND_REQUEST: ["退款", "退货", "退钱"],
            TaskType.EXCHANGE_REQUEST: ["换货", "更换", "换一个"],
            TaskType.COMPLAINT: ["投诉", "举报", "不满意", "太慢", "骗子", "垃圾"],
            TaskType.GENERAL_INQUIRY: ["咨询", "问一下", "请问"]
        }

    def classify_task(self, message: str) -> TaskType:
        """分类任务类型"""
        message_lower = message.lower()

        # 优先检查投诉（优先级最高）
        for keyword in self.keywords[TaskType.COMPLAINT]:
            if keyword in message_lower:
                return TaskType.COMPLAINT

        # 检查退换货
        for keyword in self.keywords[TaskType.REFUND_REQUEST]:
            if keyword in message_lower:
                return TaskType.REFUND_REQUEST

        for keyword in self.keywords[TaskType.EXCHANGE_REQUEST]:
            if keyword in message_lower:
                return TaskType.EXCHANGE_REQUEST

        # 检查订单查询
        for keyword in self.keywords[TaskType.ORDER_QUERY]:
            if keyword in message_lower:
                return TaskType.ORDER_QUERY

        for keyword in self.keywords[TaskType.ORDER_STATUS]:
            if keyword in message_lower:
                return TaskType.ORDER_STATUS

        return TaskType.GENERAL_INQUIRY

    def extract_order_id(self, message: str) -> Optional[str]:
        """提取订单号"""
        # 匹配 ORD + 数字 格式
        match = re.search(r'ORD\d+', message.upper())
        if match:
            return match.group()
        return None

    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        message = input_data.get("message", "")
        task_type = self.classify_task(message)
        order_id = self.extract_order_id(message)

        # 确定下一个处理Agent
        next_agent_map = {
            TaskType.ORDER_QUERY: AgentRole.ORDER,
            TaskType.ORDER_STATUS: AgentRole.ORDER,
            TaskType.REFUND_REQUEST: AgentRole.REFUND,
            TaskType.EXCHANGE_REQUEST: AgentRole.REFUND,
            TaskType.COMPLAINT: AgentRole.COMPLAINT,
            TaskType.GENERAL_INQUIRY: AgentRole.ORDER
        }

        return AgentResponse(
            agent_role=self.role,
            message=f"已识别任务类型: {task_type.value}",
            action_taken="任务分类与路由",
            data={
                "task_type": task_type.value,
                "order_id": order_id,
                "original_message": message
            },
            next_agent=next_agent_map.get(task_type)
        )


class OrderAgent(BaseAgent):
    """订单Agent - 处理订单查询"""

    def __init__(self):
        super().__init__(AgentRole.ORDER)

    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        order_id = input_data.get("order_id")
        customer_id = input_data.get("customer_id")

        if order_id:
            order = self.db.get_order(order_id)
            if order:
                message = self._format_order_info(order)
                return AgentResponse(
                    agent_role=self.role,
                    message=message,
                    action_taken="查询订单详情",
                    data={"order": order},
                    next_agent=None
                )
            else:
                return AgentResponse(
                    agent_role=self.role,
                    message=f"未找到订单 {order_id}，请核实订单号是否正确。",
                    action_taken="订单查询失败",
                    data={"error": "订单不存在"},
                    next_agent=None
                )

        if customer_id:
            orders = self.db.get_customer_orders(customer_id)
            if orders:
                message = f"您共有 {len(orders)} 个订单：\n"
                for o in orders:
                    message += f"- {o['order_id']}: {o['product_name']} ({o['status']})\n"
                return AgentResponse(
                    agent_role=self.role,
                    message=message,
                    action_taken="查询客户订单列表",
                    data={"orders": orders},
                    next_agent=None
                )

        return AgentResponse(
            agent_role=self.role,
            message="请提供订单号以便查询，格式如：ORD001",
            action_taken="等待订单号",
            data={},
            next_agent=None
        )

    def _format_order_info(self, order: dict) -> str:
        """格式化订单信息"""
        return f"""📦 订单信息
━━━━━━━━━━━━━━━━━━
订单号: {order['order_id']}
商品: {order['product_name']}
金额: ¥{order['price']}
状态: {order['status']}
━━━━━━━━━━━━━━━━━━
🚚 物流信息
物流状态: {order['shipping_status']}
运单号: {order.get('tracking_number', '暂无')}
预计送达: {order.get('estimated_delivery', '待定')}"""


class RefundAgent(BaseAgent):
    """退换货Agent - 处理退换货申请"""

    def __init__(self):
        super().__init__(AgentRole.REFUND)

    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        order_id = input_data.get("order_id")
        task_type = input_data.get("task_type", "refund_request")
        reason = input_data.get("reason", "客户申请")
        message = input_data.get("original_message", "")

        if not order_id:
            return AgentResponse(
                agent_role=self.role,
                message="请提供需要退换货的订单号。",
                action_taken="等待订单号",
                data={},
                next_agent=None
            )

        order = self.db.get_order(order_id)
        if not order:
            return AgentResponse(
                agent_role=self.role,
                message=f"未找到订单 {order_id}",
                action_taken="订单验证失败",
                data={"error": "订单不存在"},
                next_agent=None
            )

        # 检查是否可以退换货
        if order["status"] == "已完成" or order["shipping_status"] == "已签收":
            # 创建退换货申请
            refund_type = "换货" if "exchange" in task_type else "退款"
            refund = self.db.create_refund(order_id, reason, refund_type)

            response_message = f"""✅ {refund_type}申请已受理
━━━━━━━━━━━━━━━━━━
申请单号: {refund['refund_id']}
订单号: {order_id}
商品: {order['product_name']}
{refund_type}金额: ¥{refund['amount']}
预计处理完成: {refund['estimated_completion']}
━━━━━━━━━━━━━━━━━━
我们将在1-3个工作日内处理您的申请。"""

            return AgentResponse(
                agent_role=self.role,
                message=response_message,
                action_taken=f"创建{refund_type}申请",
                data={"refund": refund, "order": order},
                next_agent=None
            )
        else:
            return AgentResponse(
                agent_role=self.role,
                message=f"订单 {order_id} 当前状态为「{order['status']}」，暂时无法申请退换货。请等待收货后再申请。",
                action_taken="退换货条件检查",
                data={"order": order, "can_refund": False},
                next_agent=None
            )


class ComplaintAgent(BaseAgent):
    """投诉Agent - 处理投诉升级"""

    def __init__(self):
        super().__init__(AgentRole.COMPLAINT)

    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        order_id = input_data.get("order_id")
        customer_id = input_data.get("customer_id", "C001")
        message = input_data.get("original_message", "客户投诉")

        # 分析投诉类型
        complaint_type = self._analyze_complaint_type(message)

        # 创建投诉记录
        complaint = self.db.create_complaint(
            customer_id=customer_id,
            order_id=order_id or "",
            complaint_type=complaint_type,
            content=message
        )

        response_message = f"""🔔 投诉已受理
━━━━━━━━━━━━━━━━━━
投诉单号: {complaint['complaint_id']}
投诉类型: {complaint_type}
优先级: {complaint['priority']}
处理人: {complaint['assigned_to']}
━━━━━━━━━━━━━━━━━━
我们非常重视您的反馈！高级客服专员将在2小时内与您联系。

如需紧急处理，请拨打客服热线：400-XXX-XXXX"""

        return AgentResponse(
            agent_role=self.role,
            message=response_message,
            action_taken="创建投诉工单并升级",
            data={"complaint": complaint},
            next_agent=AgentRole.SUPERVISOR
        )

    def _analyze_complaint_type(self, message: str) -> str:
        """分析投诉类型"""
        if any(w in message for w in ["物流", "快递", "发货", "太慢"]):
            return "物流投诉"
        elif any(w in message for w in ["质量", "坏了", "损坏"]):
            return "商品质量投诉"
        elif any(w in message for w in ["服务", "态度"]):
            return "服务态度投诉"
        else:
            return "一般投诉"


class SupervisorAgent(BaseAgent):
    """主管Agent - 监督协调和最终审核"""

    def __init__(self):
        super().__init__(AgentRole.SUPERVISOR)

    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        complaint = input_data.get("complaint", {})

        # 主管审核并添加处理意见
        supervisor_note = "已审核，安排专人跟进处理。"

        if complaint.get("priority") == "高":
            supervisor_note = "高优先级投诉，已安排高级专员优先处理，预计1小时内回电。"

        return AgentResponse(
            agent_role=self.role,
            message=f"📋 主管审核完成\n{supervisor_note}",
            action_taken="主管审核",
            data={
                "supervisor_note": supervisor_note,
                "escalation_level": "已升级至主管"
            },
            next_agent=None
        )

