"""
智能客服中心专用数据模型
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
import uuid


class CustomerLevel(str, Enum):
    """客户等级"""
    NORMAL = "normal"        # 普通客户
    SILVER = "silver"        # 银卡客户
    GOLD = "gold"           # 金卡客户
    DIAMOND = "diamond"      # 钻石客户


class TicketCategory(str, Enum):
    """工单分类"""
    ORDER_ISSUE = "order_issue"          # 订单问题
    LOGISTICS_ISSUE = "logistics_issue"    # 物流问题
    REFUND_RETURN = "refund_return"        # 退换货
    TECHNICAL_SUPPORT = "tech_support"     # 技术支持
    COMPLAINT = "complaint"               # 投诉建议
    ACCOUNT_ISSUE = "account_issue"        # 账户问题
    PRODUCT_INQUIRY = "product_inquiry"    # 产品咨询
    PAYMENT_ISSUE = "payment_issue"        # 支付问题
    OTHER = "other"                       # 其他


class TicketPriority(str, Enum):
    """工单优先级"""
    LOW = "low"           # 低优先级
    MEDIUM = "medium"     # 中等优先级
    HIGH = "high"         # 高优先级
    URGENT = "urgent"     # 紧急


class TicketStatus(str, Enum):
    """工单状态"""
    PENDING = "pending"           # 待处理
    PROCESSING = "processing"     # 处理中
    RESOLVED = "resolved"         # 已解决
    CLOSED = "closed"            # 已关闭
    ESCALATED = "escalated"       # 已升级


class AgentStatus(str, Enum):
    """客服专员状态"""
    ONLINE = "online"       # 在线
    BUSY = "busy"          # 忙碌
    OFFLINE = "offline"    # 离线
    BREAK = "break"        # 休息中


class ChannelType(str, Enum):
    """接入渠道"""
    WEB = "web"           # Web聊天
    APP = "app"           # APP
    WECHAT = "wechat"     # 微信
    PHONE = "phone"       # 电话
    EMAIL = "email"       # 邮件
    SMS = "sms"          # 短信


class Customer(BaseModel):
    """客户信息模型"""
    customer_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    member_level: CustomerLevel = CustomerLevel.NORMAL

    # 统计信息
    total_orders: int = 0
    total_complaints: int = 0
    total_tickets: int = 0
    satisfaction_score: float = 0.0  # 0-5分

    # 标签和画像
    tags: List[str] = []
    preferences: Dict[str, Any] = {}

    # 时间记录
    first_contact: Optional[datetime] = None
    last_contact: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # 元数据
    metadata: Dict[str, Any] = {}


class Ticket(BaseModel):
    """工单模型"""
    ticket_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str

    # 工单基本信息
    title: str
    description: str
    category: TicketCategory
    priority: TicketPriority = TicketPriority.MEDIUM
    status: TicketStatus = TicketStatus.PENDING

    # 分配信息
    assigned_agent: Optional[str] = None
    assigned_department: Optional[str] = None

    # 渠道信息
    channel: ChannelType = ChannelType.WEB
    channel_session_id: Optional[str] = None

    # 时间记录
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    due_date: Optional[datetime] = None  # 预期解决时间

    # 满意度评价
    satisfaction_rating: Optional[int] = None  # 1-5
    feedback: Optional[str] = None

    # 关联信息
    related_order_id: Optional[str] = None
    related_product_id: Optional[str] = None

    # 处理记录
    resolution: Optional[str] = None  # 解决方案
    internal_notes: List[str] = []    # 内部备注

    # 元数据
    metadata: Dict[str, Any] = {}


class Agent(BaseModel):
    """客服专员模型"""
    agent_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    phone: Optional[str] = None

    # 技能和专业领域
    skills: List[str] = []
    specialties: List[TicketCategory] = []

    # 工作状态
    status: AgentStatus = AgentStatus.OFFLINE
    current_tickets: List[str] = []  # 当前处理的工单ID
    max_tickets: int = 10

    # 绩效指标
    average_response_time: float = 0.0  # 平均响应时间（分钟）
    average_resolution_time: float = 0.0  # 平均解决时间（小时）
    satisfaction_score: float = 0.0  # 客户满意度
    tickets_resolved: int = 0       # 已解决工单数
    tickets_handled: int = 0        # 总处理工单数

    # 工作时间
    working_hours: Dict[str, Any] = {}  # 工作时间配置
    last_active: Optional[datetime] = None

    # 时间记录
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # 元数据
    metadata: Dict[str, Any] = {}


class CustomerServiceTaskType(str, Enum):
    """客服专用任务类型"""
    ORDER_QUERY = "order_query"          # 订单查询
    ORDER_MODIFY = "order_modify"        # 订单修改
    ORDER_CANCEL = "order_cancel"        # 订单取消
    REFUND_REQUEST = "refund_request"    # 退款申请
    RETURN_EXCHANGE = "return_exchange"  # 退换货
    LOGISTICS_TRACKING = "logistics"     # 物流查询
    PRODUCT_INFO = "product_info"        # 产品信息
    TECHNICAL_SUPPORT = "tech_support"   # 技术支持
    COMPLAINT_HANDLING = "complaint"     # 投诉处理
    ACCOUNT_ISSUES = "account"           # 账户问题
    PAYMENT_ISSUES = "payment"           # 支付问题
    CONSULTATION = "consultation"        # 咨询服务
    ESCALATION = "escalation"           # 问题升级


class KnowledgeBase(BaseModel):
    """知识库条目"""
    kb_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category: TicketCategory
    title: str
    content: str
    keywords: List[str] = []

    # 使用统计
    usage_count: int = 0
    helpful_count: int = 0

    # 状态
    is_active: bool = True
    version: int = 1

    # 时间记录
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    last_used: Optional[datetime] = None

    # 作者和审核
    author: str
    reviewer: Optional[str] = None

    # 元数据
    metadata: Dict[str, Any] = {}


class CustomerServiceMessage(BaseModel):
    """客服消息模型"""
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ticket_id: str
    sender_id: str  # 发送者ID（客户或客服）
    sender_type: str  # "customer" or "agent" or "system"
    content: str

    # 消息类型
    message_type: str = "text"  # text, image, file, system

    # 关联信息
    channel: ChannelType = ChannelType.WEB

    # 时间记录
    timestamp: datetime = Field(default_factory=datetime.now)

    # 状态
    read_at: Optional[datetime] = None

    # 元数据
    metadata: Dict[str, Any] = {}


class CustomerServiceMetrics(BaseModel):
    """客服绩效指标"""
    agent_id: str
    date: datetime

    # 基础指标
    tickets_handled: int = 0
    tickets_resolved: int = 0
    response_time_avg: float = 0.0  # 平均响应时间（分钟）
    resolution_time_avg: float = 0.0  # 平均解决时间（小时）

    # 质量指标
    satisfaction_score: float = 0.0
    first_contact_resolution: float = 0.0  # 首次解决率

    # 效率指标
    tickets_per_hour: float = 0.0
    chat_duration_avg: float = 0.0

    # 分类统计
    tickets_by_category: Dict[str, int] = {}
    tickets_by_priority: Dict[str, int] = {}

    # 元数据
    metadata: Dict[str, Any] = {}


# 请求和响应模型
class CreateTicketRequest(BaseModel):
    """创建工单请求"""
    customer_id: Optional[str] = None
    customer_info: Optional[Dict[str, Any]] = None  # 如果是新客户
    title: str
    description: str
    category: TicketCategory
    priority: TicketPriority = TicketPriority.MEDIUM
    channel: ChannelType = ChannelType.WEB
    related_order_id: Optional[str] = None
    related_product_id: Optional[str] = None


class CreateTicketResponse(BaseModel):
    """创建工单响应"""
    success: bool
    ticket_id: Optional[str] = None
    message: str
    estimated_resolution_time: Optional[str] = None


class TicketUpdateRequest(BaseModel):
    """工单更新请求"""
    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None
    assigned_agent: Optional[str] = None
    resolution: Optional[str] = None
    internal_notes: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class CustomerLookupRequest(BaseModel):
    """客户查询请求"""
    query: str  # 手机号、邮箱、姓名等
    search_type: str = "phone"  # phone, email, name, customer_id


class AgentAssignmentRequest(BaseModel):
    """客服分配请求"""
    ticket_id: str
    agent_id: Optional[str] = None  # 如果为空则自动分配
    assignment_reason: Optional[str] = None


class EscalationRequest(BaseModel):
    """问题升级请求"""
    ticket_id: str
    escalation_reason: str
    target_department: str
    urgency_level: TicketPriority
    additional_info: Optional[str] = None