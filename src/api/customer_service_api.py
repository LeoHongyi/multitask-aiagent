"""
智能客服中心专用API接口
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Optional
from datetime import datetime
import logging

from schemas.customer_service_models import (
    CreateTicketRequest, CreateTicketResponse, TicketUpdateRequest,
    CustomerLookupRequest, AgentAssignmentRequest, EscalationRequest,
    Ticket, Customer, Agent, CustomerServiceTaskType, ChannelType
)
from core.customer_service_agent import CustomerServiceAgent
from utils.redis_manager import RedisManager

# 创建路由器
router = APIRouter(prefix="/customer-service", tags=["智能客服中心"])
logger = logging.getLogger(__name__)

# 全局变量（在main.py中初始化）
cs_agent: Optional[CustomerServiceAgent] = None
redis_manager: Optional[RedisManager] = None


def get_cs_agent() -> CustomerServiceAgent:
    """获取客服Agent实例"""
    global cs_agent
    if cs_agent is None:
        cs_agent = CustomerServiceAgent()
    return cs_agent


def get_redis_manager() -> RedisManager:
    """获取Redis管理器实例"""
    global redis_manager
    if redis_manager is None:
        redis_manager = RedisManager()
    return redis_manager


@router.post("/chat", summary="智能客服对话")
async def customer_service_chat(
    query: str,
    session_id: Optional[str] = None,
    channel: ChannelType = ChannelType.WEB,
    agent: CustomerServiceAgent = Depends(get_cs_agent),
    redis: RedisManager = Depends(get_redis_manager)
):
    """
    智能客服对话接口

    Args:
        query: 客户查询内容
        session_id: 会话ID（可选）
        channel: 接入渠道

    Returns:
        客服回复结果
    """
    try:
        logger.info(f"客服对话请求: {query[:50]}...")

        # 处理查询
        result = await agent.process_customer_service_query(query)

        # 如果有会话ID，保存对话历史
        if session_id:
            try:
                # 保存客户消息
                await redis.cache_result(
                    f"cs_session:{session_id}:customer",
                    {"query": query, "timestamp": datetime.now().isoformat()},
                    ttl=86400  # 24小时
                )

                # 保存客服回复
                await redis.cache_result(
                    f"cs_session:{session_id}:agent",
                    {"response": result["response"], "timestamp": datetime.now().isoformat()},
                    ttl=86400
                )
            except Exception as e:
                logger.warning(f"保存会话历史失败: {e}")

        # 添加会话信息
        result["session_id"] = session_id
        result["channel"] = channel

        return result

    except Exception as e:
        logger.error(f"客服对话处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"客服对话处理失败: {str(e)}")


@router.post("/tickets", response_model=CreateTicketResponse, summary="创建工单")
async def create_ticket(
    request: CreateTicketRequest,
    agent: CustomerServiceAgent = Depends(get_cs_agent),
    redis: RedisManager = Depends(get_redis_manager)
):
    """
    创建新的客服工单

    Args:
        request: 工单创建请求

    Returns:
        工单创建结果
    """
    try:
        logger.info(f"创建工单请求: {request.title}")

        # 如果是新客户，先创建客户信息
        customer_id = request.customer_id
        if not customer_id and request.customer_info:
            # 这里应该创建新客户，简化处理直接生成ID
            import uuid
            customer_id = f"CUST{uuid.uuid4().hex[:8]}"

            # 保存客户信息
            customer_data = {
                "customer_id": customer_id,
                **request.customer_info,
                "created_at": datetime.now().isoformat()
            }

            try:
                await redis.cache_result(
                    f"customer:{customer_id}",
                    customer_data,
                    ttl=2592000  # 30天
                )
            except Exception as e:
                logger.warning(f"保存客户信息失败: {e}")

        # 调用工单创建工具
        from tools.customer_service_tools import execute_customer_service_tool

        tool_result = await execute_customer_service_tool("ticket_create", {
            "customer_id": customer_id,
            "title": request.title,
            "description": request.description,
            "category": request.category.value,
            "priority": request.priority.value,
            "channel": request.channel.value,
            "related_order_id": request.related_order_id,
            "related_product_id": request.related_product_id
        })

        if tool_result.get("success"):
            # 保存工单信息
            ticket_data = {
                "ticket_id": tool_result.get("ticket_id"),
                "customer_id": customer_id,
                **request.dict(),
                "status": "pending",
                "created_at": datetime.now().isoformat()
            }

            try:
                await redis.cache_result(
                    f"ticket:{tool_result.get('ticket_id')}",
                    ticket_data,
                    ttl=604800  # 7天
                )
            except Exception as e:
                logger.warning(f"保存工单信息失败: {e}")

            return CreateTicketResponse(
                success=True,
                ticket_id=tool_result.get("ticket_id"),
                message=tool_result.get("message"),
                estimated_resolution_time=tool_result.get("estimated_resolution")
            )
        else:
            return CreateTicketResponse(
                success=False,
                message=tool_result.get("message", "工单创建失败")
            )

    except Exception as e:
        logger.error(f"创建工单失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建工单失败: {str(e)}")


@router.get("/tickets/{ticket_id}", summary="查询工单")
async def get_ticket(
    ticket_id: str,
    redis: RedisManager = Depends(get_redis_manager)
):
    """
    查询工单详情

    Args:
        ticket_id: 工单ID

    Returns:
        工单详细信息
    """
    try:
        # 从Redis获取工单信息
        ticket_data = await redis.get_cached_result(f"ticket:{ticket_id}")

        if not ticket_data:
            raise HTTPException(status_code=404, detail="工单不存在")

        return {
            "success": True,
            "ticket": ticket_data
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询工单失败: {e}")
        raise HTTPException(status_code=500, detail=f"查询工单失败: {str(e)}")


@router.put("/tickets/{ticket_id}", summary="更新工单")
async def update_ticket(
    ticket_id: str,
    request: TicketUpdateRequest,
    redis: RedisManager = Depends(get_redis_manager)
):
    """
    更新工单状态和信息

    Args:
        ticket_id: 工单ID
        request: 更新请求

    Returns:
        更新结果
    """
    try:
        # 获取现有工单信息
        ticket_data = await redis.get_cached_result(f"ticket:{ticket_id}")

        if not ticket_data:
            raise HTTPException(status_code=404, detail="工单不存在")

        # 更新字段
        if request.status:
            ticket_data["status"] = request.status.value
            if request.status.value == "resolved":
                ticket_data["resolved_at"] = datetime.now().isoformat()

        if request.priority:
            ticket_data["priority"] = request.priority.value

        if request.assigned_agent:
            ticket_data["assigned_agent"] = request.assigned_agent

        if request.resolution:
            ticket_data["resolution"] = request.resolution

        if request.internal_notes:
            ticket_data["internal_notes"] = request.internal_notes

        ticket_data["updated_at"] = datetime.now().isoformat()

        # 保存更新后的信息
        await redis.cache_result(
            f"ticket:{ticket_id}",
            ticket_data,
            ttl=604800  # 7天
        )

        return {
            "success": True,
            "message": "工单更新成功",
            "ticket": ticket_data
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新工单失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新工单失败: {str(e)}")


@router.post("/customers/lookup", summary="客户查询")
async def lookup_customer(
    request: CustomerLookupRequest,
    redis: RedisManager = Depends(get_redis_manager)
):
    """
    查询客户信息

    Args:
        request: 查询请求

    Returns:
        客户信息
    """
    try:
        # 调用客户查询工具
        from tools.customer_service_tools import execute_customer_service_tool

        # 构建查询参数
        params = {"query": request.query}
        if request.search_type == "phone":
            params["phone"] = request.query
        elif request.search_type == "email":
            params["email"] = request.query
        elif request.search_type == "name":
            params["name"] = request.query
        elif request.search_type == "customer_id":
            params["customer_id"] = request.query

        result = await execute_customer_service_tool("customer_lookup", params)

        return result

    except Exception as e:
        logger.error(f"客户查询失败: {e}")
        return {
            "success": False,
            "message": f"客户查询失败: {str(e)}"
        }


@router.get("/customers/{customer_id}/tickets", summary="客户工单历史")
async def get_customer_tickets(
    customer_id: str,
    limit: int = 10,
    redis: RedisManager = Depends(get_redis_manager)
):
    """
    获取客户的历史工单

    Args:
        customer_id: 客户ID
        limit: 返回数量限制

    Returns:
        工单列表
    """
    try:
        # 这里应该从数据库查询，简化处理返回模拟数据
        mock_tickets = [
            {
                "ticket_id": "TK20251207001",
                "title": "订单物流查询",
                "category": "logistics_issue",
                "status": "resolved",
                "created_at": "2025-12-07T10:30:00",
                "resolved_at": "2025-12-07T11:15:00"
            },
            {
                "ticket_id": "TK20251206001",
                "title": "产品咨询",
                "category": "product_inquiry",
                "status": "closed",
                "created_at": "2025-12-06T14:20:00",
                "closed_at": "2025-12-06T14:45:00"
            }
        ]

        return {
            "success": True,
            "customer_id": customer_id,
            "tickets": mock_tickets[:limit],
            "total": len(mock_tickets)
        }

    except Exception as e:
        logger.error(f"查询客户工单失败: {e}")
        raise HTTPException(status_code=500, detail=f"查询客户工单失败: {str(e)}")


@router.get("/agents/stats", summary="客服统计")
async def get_agent_stats(
    agent_id: Optional[str] = None,
    date: Optional[str] = None,
    redis: RedisManager = Depends(get_redis_manager)
):
    """
    获取客服专员统计信息

    Args:
        agent_id: 客服ID（可选）
        date: 日期（可选，格式：YYYY-MM-DD）

    Returns:
        统计信息
    """
    try:
        # 模拟统计数据
        mock_stats = {
            "agent_id": agent_id or "all",
            "date": date or datetime.now().strftime("%Y-%m-%d"),
            "tickets_handled": 15,
            "tickets_resolved": 12,
            "response_time_avg": 2.5,  # 分钟
            "resolution_time_avg": 4.2,  # 小时
            "satisfaction_score": 4.3,
            "first_contact_resolution": 0.8,  # 80%
            "tickets_by_category": {
                "order_issue": 5,
                "logistics_issue": 3,
                "refund_return": 2,
                "tech_support": 3,
                "other": 2
            },
            "tickets_by_priority": {
                "urgent": 1,
                "high": 3,
                "medium": 8,
                "low": 3
            }
        }

        return {
            "success": True,
            "stats": mock_stats
        }

    except Exception as e:
        logger.error(f"获取客服统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取客服统计失败: {str(e)}")


@router.post("/escalations", summary="问题升级")
async def create_escalation(
    request: EscalationRequest,
    redis: RedisManager = Depends(get_redis_manager)
):
    """
    创建问题升级请求

    Args:
        request: 升级请求

    Returns:
        升级结果
    """
    try:
        import uuid
        escalation_id = f"ESC{uuid.uuid4().hex[:8]}"

        escalation_data = {
            "escalation_id": escalation_id,
            "ticket_id": request.ticket_id,
            "escalation_reason": request.escalation_reason,
            "target_department": request.target_department,
            "urgency_level": request.urgency_level.value,
            "additional_info": request.additional_info,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }

        # 保存升级信息
        await redis.cache_result(
            f"escalation:{escalation_id}",
            escalation_data,
            ttl=604800  # 7天
        )

        return {
            "success": True,
            "escalation_id": escalation_id,
            "message": "问题升级请求已提交，相关部门会尽快处理",
            "estimated_response_time": "2小时内"
        }

    except Exception as e:
        logger.error(f"创建问题升级失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建问题升���失败: {str(e)}")


@router.get("/knowledge/search", summary="知识库搜索")
async def search_knowledge(
    query: str,
    category: Optional[str] = None,
    limit: int = 5,
    redis: RedisManager = Depends(get_redis_manager)
):
    """
    搜索知识库

    Args:
        query: 搜索关键词
        category: 分类过滤（可选）
        limit: 返回结果数量限制

    Returns:
        知识库搜索结果
    """
    try:
        from tools.customer_service_tools import execute_customer_service_tool

        result = await execute_customer_service_tool("knowledge_search", {
            "query": query,
            "category": category,
            "limit": limit
        })

        return result

    except Exception as e:
        logger.error(f"知识库搜索失败: {e}")
        return {
            "success": False,
            "message": f"知识库搜索失败: {str(e)}"
        }


@router.get("/health", summary="客服系统健康检查")
async def health_check():
    """
    客服系统健康检查

    Returns:
        系统状态信息
    """
    try:
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "customer_service_agent": "running",
                "tools": "available",
                "redis": "connected"
            },
            "version": "1.0.0"
        }

    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }