"""
模拟数据库 - 订单、客户、退换货记录
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import random

# 模拟订单数据
MOCK_ORDERS: Dict[str, dict] = {
    "ORD001": {
        "order_id": "ORD001",
        "customer_id": "C001",
        "product_name": "iPhone 15 Pro",
        "quantity": 1,
        "price": 8999.00,
        "status": "已发货",
        "created_at": "2025-12-01 10:30:00",
        "shipping_status": "运输中",
        "tracking_number": "SF1234567890",
        "estimated_delivery": "2025-12-08"
    },
    "ORD002": {
        "order_id": "ORD002",
        "customer_id": "C001",
        "product_name": "AirPods Pro 2",
        "quantity": 1,
        "price": 1899.00,
        "status": "已完成",
        "created_at": "2025-11-20 14:20:00",
        "shipping_status": "已签收",
        "tracking_number": "SF0987654321",
        "estimated_delivery": "2025-11-25"
    },
    "ORD003": {
        "order_id": "ORD003",
        "customer_id": "C002",
        "product_name": "MacBook Air M3",
        "quantity": 1,
        "price": 9499.00,
        "status": "待发货",
        "created_at": "2025-12-05 09:15:00",
        "shipping_status": "仓库处理中",
        "tracking_number": None,
        "estimated_delivery": "2025-12-10"
    },
    "ORD004": {
        "order_id": "ORD004",
        "customer_id": "C003",
        "product_name": "iPad Pro 12.9",
        "quantity": 1,
        "price": 8499.00,
        "status": "已发货",
        "created_at": "2025-12-03 16:45:00",
        "shipping_status": "派送中",
        "tracking_number": "YT9876543210",
        "estimated_delivery": "2025-12-07"
    },
}

# 模拟客户数据
MOCK_CUSTOMERS: Dict[str, dict] = {
    "C001": {
        "customer_id": "C001",
        "name": "张三",
        "email": "zhangsan@example.com",
        "phone": "138****1234",
        "vip_level": 3,
        "total_orders": 15,
        "registered_at": "2023-05-10"
    },
    "C002": {
        "customer_id": "C002",
        "name": "李四",
        "email": "lisi@example.com",
        "phone": "139****5678",
        "vip_level": 1,
        "total_orders": 3,
        "registered_at": "2025-01-15"
    },
    "C003": {
        "customer_id": "C003",
        "name": "王五",
        "email": "wangwu@example.com",
        "phone": "137****9012",
        "vip_level": 2,
        "total_orders": 8,
        "registered_at": "2024-03-20"
    },
}

# 模拟退换货记录
MOCK_REFUNDS: Dict[str, dict] = {
    "RF001": {
        "refund_id": "RF001",
        "order_id": "ORD002",
        "customer_id": "C001",
        "type": "退款",
        "reason": "商品质量问题",
        "status": "处理中",
        "amount": 1899.00,
        "created_at": "2025-12-05 11:00:00"
    }
}

# 模拟投诉记录
MOCK_COMPLAINTS: Dict[str, dict] = {
    "CP001": {
        "complaint_id": "CP001",
        "customer_id": "C002",
        "order_id": "ORD003",
        "type": "物流投诉",
        "content": "订单迟迟不发货",
        "status": "待处理",
        "priority": "高",
        "created_at": "2025-12-06 14:30:00"
    }
}


class MockDatabase:
    """模拟数据库操作"""

    @staticmethod
    def get_order(order_id: str) -> Optional[dict]:
        """获取订单"""
        return MOCK_ORDERS.get(order_id)

    @staticmethod
    def get_customer_orders(customer_id: str) -> List[dict]:
        """获取客户所有订单"""
        return [o for o in MOCK_ORDERS.values() if o["customer_id"] == customer_id]

    @staticmethod
    def get_customer(customer_id: str) -> Optional[dict]:
        """获取客户信息"""
        return MOCK_CUSTOMERS.get(customer_id)

    @staticmethod
    def create_refund(order_id: str, reason: str, refund_type: str = "退款") -> dict:
        """创建退换货申请"""
        order = MOCK_ORDERS.get(order_id)
        if not order:
            return {"error": "订单不存在"}

        refund_id = f"RF{random.randint(100, 999)}"
        refund = {
            "refund_id": refund_id,
            "order_id": order_id,
            "customer_id": order["customer_id"],
            "type": refund_type,
            "reason": reason,
            "status": "已受理",
            "amount": order["price"],
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "estimated_completion": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
        }
        MOCK_REFUNDS[refund_id] = refund
        return refund

    @staticmethod
    def create_complaint(customer_id: str, order_id: str, complaint_type: str, content: str) -> dict:
        """创建投诉"""
        complaint_id = f"CP{random.randint(100, 999)}"
        complaint = {
            "complaint_id": complaint_id,
            "customer_id": customer_id,
            "order_id": order_id,
            "type": complaint_type,
            "content": content,
            "status": "已受理",
            "priority": "高",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "assigned_to": "高级客服专员"
        }
        MOCK_COMPLAINTS[complaint_id] = complaint
        return complaint

    @staticmethod
    def get_refund(refund_id: str) -> Optional[dict]:
        """获取退换货记录"""
        return MOCK_REFUNDS.get(refund_id)

    @staticmethod
    def get_order_refunds(order_id: str) -> List[dict]:
        """获取订单相关的退换货记录"""
        return [r for r in MOCK_REFUNDS.values() if r["order_id"] == order_id]

