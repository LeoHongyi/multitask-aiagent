"""
多Agent协同客服系统 - 数据模型
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class AgentRole(str, Enum):
    """Agent角色"""
    ROUTER = "router"           # 路由Agent - 任务分发
    ORDER = "order"             # 订单Agent - 订单查询
    REFUND = "refund"           # 退换货Agent - 退换货处理
    COMPLAINT = "complaint"     # 投诉Agent - 投诉升级
    SUPERVISOR = "supervisor"   # 主管Agent - 监督协调


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"         # 待处理
    PROCESSING = "processing"   # 处理中
    ESCALATED = "escalated"     # 已升级
    COMPLETED = "completed"     # 已完成
    FAILED = "failed"           # 失败


class TaskType(str, Enum):
    """任务类型"""
    ORDER_QUERY = "order_query"           # 订单查询
    ORDER_STATUS = "order_status"         # 订单状态
    REFUND_REQUEST = "refund_request"     # 退款申请
    EXCHANGE_REQUEST = "exchange_request" # 换货申请
    COMPLAINT = "complaint"               # 投诉
    GENERAL_INQUIRY = "general_inquiry"   # 一般咨询


class WorkflowStep(BaseModel):
    """工作流步骤"""
    step_id: str
    agent_role: AgentRole
    action: str
    input_data: Dict[str, Any] = {}
    output_data: Dict[str, Any] = {}
    status: TaskStatus = TaskStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class Workflow(BaseModel):
    """工作流"""
    workflow_id: str
    task_type: TaskType
    steps: List[WorkflowStep] = []
    current_step: int = 0
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class CustomerRequest(BaseModel):
    """客户请求"""
    message: str
    customer_id: Optional[str] = None
    order_id: Optional[str] = None
    session_id: Optional[str] = None


class AgentResponse(BaseModel):
    """Agent响应"""
    agent_role: AgentRole
    message: str
    action_taken: str
    data: Dict[str, Any] = {}
    next_agent: Optional[AgentRole] = None


class WorkflowResponse(BaseModel):
    """工作流响应"""
    workflow_id: str
    task_type: TaskType
    status: TaskStatus
    responses: List[AgentResponse]
    final_response: str
    steps_completed: int
    total_steps: int


# ==================== 模拟数据 ====================

class MockOrder(BaseModel):
    """模拟订单"""
    order_id: str
    customer_id: str
    product_name: str
    quantity: int
    price: float
    status: str
    created_at: str
    shipping_status: str
    tracking_number: Optional[str] = None


class MockCustomer(BaseModel):
    """模拟客户"""
    customer_id: str
    name: str
    email: str
    phone: str
    vip_level: int
    total_orders: int

