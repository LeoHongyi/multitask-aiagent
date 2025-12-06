"""
多Agent协同客服系统 - 基于 LangGraph 的工作流实现
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, TypedDict, Annotated, Literal
from datetime import datetime
import uuid
import os
import json
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# LangGraph 和 LangChain 导入
try:
    from langgraph.graph import StateGraph, END
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    print("⚠️ LangGraph 未安装，将使用降级模式")

router = APIRouter(prefix="/api/agent", tags=["多Agent客服系统"])


# ==================== 数据模型 ====================

class CustomerServiceRequest(BaseModel):
    """客服请求"""
    message: str
    customer_id: Optional[str] = "C001"
    order_id: Optional[str] = None


# ==================== 模拟数据 ====================

MOCK_ORDERS = {
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

MOCK_CUSTOMERS = {
    "C001": {"customer_id": "C001", "name": "张三", "phone": "138****1234", "vip_level": 3},
    "C002": {"customer_id": "C002", "name": "李四", "phone": "139****5678", "vip_level": 1},
    "C003": {"customer_id": "C003", "name": "王五", "phone": "137****9012", "vip_level": 2},
}

# 存储
workflows_store = {}
refunds_store = {}
complaints_store = {}


# ==================== LangGraph 状态定义 ====================

class AgentState(TypedDict):
    """工作流状态"""
    messages: List[Dict[str, Any]]  # 消息历史
    customer_message: str           # 客户原始消息
    customer_id: str                # 客户ID
    order_id: Optional[str]         # 订单ID
    task_type: str                  # 任务类型
    current_agent: str              # 当前处理Agent
    agent_chain: List[Dict]         # Agent处理链
    response: str                   # 最终响应
    need_escalation: bool           # 是否需要升级
    workflow_id: str                # 工作流ID
    error: Optional[str]            # 错误信息


# ==================== LLM 初始化 ====================

def get_llm():
    """获取LLM实例"""
    api_key = os.getenv("OPENAI_API_KEY")
    api_base = os.getenv("OPENAI_API_BASE")

    if not api_key:
        return None

    return ChatOpenAI(
        model="gpt-3.5-turbo",
        openai_api_key=api_key,
        openai_api_base=api_base,
        temperature=0.3
    )


# ==================== Agent 节点定义 ====================

class MultiAgentWorkflow:
    """基于 LangGraph 的多Agent工作流"""

    def __init__(self):
        self.llm = get_llm()
        self.graph = self._build_graph() if LANGGRAPH_AVAILABLE else None

    def _build_graph(self) -> StateGraph:
        """构建 LangGraph 工作流图"""

        # 创建状态图
        workflow = StateGraph(AgentState)

        # 添加节点
        workflow.add_node("router_agent", self.router_agent)
        workflow.add_node("order_agent", self.order_agent)
        workflow.add_node("refund_agent", self.refund_agent)
        workflow.add_node("complaint_agent", self.complaint_agent)
        workflow.add_node("supervisor_agent", self.supervisor_agent)
        workflow.add_node("response_generator", self.response_generator)

        # 设置入口
        workflow.set_entry_point("router_agent")

        # 添加条件边 - 路由Agent决定下一步
        workflow.add_conditional_edges(
            "router_agent",
            self._route_decision,
            {
                "order": "order_agent",
                "refund": "refund_agent",
                "complaint": "complaint_agent",
                "general": "response_generator"
            }
        )

        # 订单Agent处理后
        workflow.add_conditional_edges(
            "order_agent",
            self._check_escalation,
            {
                "escalate": "supervisor_agent",
                "complete": "response_generator"
            }
        )

        # 退换货Agent处理后
        workflow.add_conditional_edges(
            "refund_agent",
            self._check_escalation,
            {
                "escalate": "supervisor_agent",
                "complete": "response_generator"
            }
        )

        # 投诉Agent处理后 - 总是升级到主管
        workflow.add_edge("complaint_agent", "supervisor_agent")

        # 主管Agent处理后
        workflow.add_edge("supervisor_agent", "response_generator")

        # 响应生成后结束
        workflow.add_edge("response_generator", END)

        return workflow.compile()

    def _route_decision(self, state: AgentState) -> str:
        """路由决策"""
        task_type = state.get("task_type", "general")
        if task_type in ["order_query", "order_status"]:
            return "order"
        elif task_type in ["refund_request", "exchange_request"]:
            return "refund"
        elif task_type == "complaint":
            return "complaint"
        return "general"

    def _check_escalation(self, state: AgentState) -> str:
        """检查是否需要升级"""
        return "escalate" if state.get("need_escalation", False) else "complete"

    # ==================== Agent 节点实现 ====================

    def router_agent(self, state: AgentState) -> AgentState:
        """路由Agent - 使用LLM分析意图"""
        message = state["customer_message"]

        if self.llm:
            # 使用LLM进行意图分析
            prompt = f"""你是一个智能客服路由系统。分析客户消息并分类任务类型。

客户消息: "{message}"

请分析并返回JSON格式:
{{
    "task_type": "order_query|refund_request|exchange_request|complaint|general",
    "extracted_order_id": "ORD开头的订单号或null",
    "sentiment": "positive|neutral|negative",
    "urgency": "low|medium|high",
    "reason": "分类原因"
}}

只返回JSON，不要其他内容。"""

            try:
                response = self.llm.invoke([HumanMessage(content=prompt)])
                result = json.loads(response.content)

                task_type = result.get("task_type", "general")
                order_id = result.get("extracted_order_id") or state.get("order_id")
                urgency = result.get("urgency", "medium")

                state["task_type"] = task_type
                state["order_id"] = order_id
                state["need_escalation"] = urgency == "high"

                state["agent_chain"].append({
                    "agent": "router",
                    "action": "LLM意图分析",
                    "message": f"任务类型: {task_type}, 紧急程度: {urgency}",
                    "llm_used": True,
                    "analysis": result
                })

            except Exception as e:
                # LLM失败，使用规则引擎
                state = self._rule_based_routing(state)
        else:
            state = self._rule_based_routing(state)

        state["current_agent"] = "router"
        return state

    def _rule_based_routing(self, state: AgentState) -> AgentState:
        """规则引擎路由（降级方案）"""
        message = state["customer_message"].lower()

        if any(w in message for w in ["投诉", "举报", "不满意", "骗子"]):
            task_type = "complaint"
        elif any(w in message for w in ["退款", "退货", "退钱"]):
            task_type = "refund_request"
        elif any(w in message for w in ["换货", "更换"]):
            task_type = "exchange_request"
        elif any(w in message for w in ["订单", "物流", "快递", "查询"]):
            task_type = "order_query"
        else:
            task_type = "general"

        # 提取订单号
        import re
        match = re.search(r'ORD\d+', state["customer_message"].upper())
        order_id = match.group() if match else state.get("order_id")

        state["task_type"] = task_type
        state["order_id"] = order_id
        state["agent_chain"].append({
            "agent": "router",
            "action": "规则引擎路由",
            "message": f"任务类型: {task_type}",
            "llm_used": False
        })

        return state

    def order_agent(self, state: AgentState) -> AgentState:
        """订单Agent - 处理订单查询"""
        order_id = state.get("order_id")
        customer_id = state.get("customer_id")

        if order_id and order_id in MOCK_ORDERS:
            order = MOCK_ORDERS[order_id]

            # 使用LLM生成自然语言回复
            if self.llm:
                prompt = f"""你是订单客服专员。根据以下订单信息，用友好专业的语气回复客户查询。

订单信息:
- 订单号: {order['order_id']}
- 商品: {order['product_name']}
- 金额: ¥{order['price']}
- 状态: {order['status']}
- 物流状态: {order['shipping_status']}
- 运单号: {order.get('tracking_number', '暂无')}
- 预计送达: {order.get('estimated_delivery', '待定')}

客户问题: {state['customer_message']}

请生成回复（使用emoji美化）:"""

                try:
                    response = self.llm.invoke([HumanMessage(content=prompt)])
                    state["response"] = response.content
                    llm_used = True
                except:
                    state["response"] = self._format_order_response(order)
                    llm_used = False
            else:
                state["response"] = self._format_order_response(order)
                llm_used = False

            state["agent_chain"].append({
                "agent": "order",
                "action": "查询订单详情",
                "message": f"已查询订单 {order_id}",
                "llm_used": llm_used,
                "data": order
            })
        else:
            # 查询客户所有订单
            orders = [o for o in MOCK_ORDERS.values() if o["customer_id"] == customer_id]
            if orders:
                state["response"] = f"您有 {len(orders)} 个订单:\n" + "\n".join(
                    f"• {o['order_id']}: {o['product_name']} ({o['status']})" for o in orders
                )
            else:
                state["response"] = "未找到相关订单，请提供正确的订单号（如ORD001）"

            state["agent_chain"].append({
                "agent": "order",
                "action": "查询客户订单列表",
                "message": f"找到 {len(orders)} 个订单",
                "llm_used": False
            })

        state["current_agent"] = "order"
        return state

    def _format_order_response(self, order: dict) -> str:
        """格式化订单响应"""
        return f"""📦 订单详情
━━━━━━━━━━━━━━━━
订单号: {order['order_id']}
商品: {order['product_name']}
金额: ¥{order['price']}
状态: {order['status']}

🚚 物流信息
状态: {order['shipping_status']}
运单号: {order.get('tracking_number', '暂无')}
预计送达: {order.get('estimated_delivery', '待定')}"""

    def refund_agent(self, state: AgentState) -> AgentState:
        """退换货Agent - 处理退换货申请"""
        order_id = state.get("order_id")
        task_type = state.get("task_type")

        if not order_id:
            state["response"] = "请提供需要退换货的订单号（如ORD001）"
            state["agent_chain"].append({
                "agent": "refund",
                "action": "等待订单号",
                "message": "缺少订单号",
                "llm_used": False
            })
            return state

        order = MOCK_ORDERS.get(order_id)
        if not order:
            state["response"] = f"未找到订单 {order_id}"
            state["agent_chain"].append({
                "agent": "refund",
                "action": "订单验证失败",
                "message": "订单不存在",
                "llm_used": False
            })
            return state

        refund_type = "换货" if "exchange" in task_type else "退款"

        # 检查退换货条件
        can_refund = order["status"] == "已完成" or order["shipping_status"] == "已签收"

        if can_refund:
            refund_id = f"RF{str(uuid.uuid4())[:6].upper()}"
            refund_record = {
                "refund_id": refund_id,
                "order_id": order_id,
                "type": refund_type,
                "amount": order["price"],
                "status": "已受理",
                "created_at": datetime.now().isoformat()
            }
            refunds_store[refund_id] = refund_record

            # 使用LLM生成回复
            if self.llm:
                prompt = f"""你是退换货客服专员。客户申请{refund_type}，已成功受理。

订单信息: {order['product_name']}, ¥{order['price']}
申请单号: {refund_id}

请生成友好专业的确认回复，包含:
1. 确认受理
2. 申请单号
3. 预计处理时间（1-3个工作日）
4. 退款方式（原路返回）

使用emoji美化:"""

                try:
                    response = self.llm.invoke([HumanMessage(content=prompt)])
                    state["response"] = response.content
                    llm_used = True
                except:
                    state["response"] = self._format_refund_response(refund_record, order, refund_type)
                    llm_used = False
            else:
                state["response"] = self._format_refund_response(refund_record, order, refund_type)
                llm_used = False

            state["agent_chain"].append({
                "agent": "refund",
                "action": f"创建{refund_type}申请",
                "message": f"申请单号: {refund_id}",
                "llm_used": llm_used,
                "data": refund_record
            })
        else:
            state["response"] = f"订单 {order_id} 状态为「{order['status']}」，暂不支持退换货。请收货后再申请。"
            state["need_escalation"] = True  # 可能需要人工介入
            state["agent_chain"].append({
                "agent": "refund",
                "action": "条件检查未通过",
                "message": "不满足退换货条件",
                "llm_used": False
            })

        state["current_agent"] = "refund"
        return state

    def _format_refund_response(self, refund: dict, order: dict, refund_type: str) -> str:
        """格式化退换货响应"""
        return f"""✅ {refund_type}申请已受理
━━━━━━━━━━━━━━━━
申请单号: {refund['refund_id']}
订单号: {refund['order_id']}
商品: {order['product_name']}
{refund_type}金额: ¥{refund['amount']}
━━━━━━━━━━━━━━━━
预计1-3个工作日内处理完成
退款将原路返回您的支付账户"""

    def complaint_agent(self, state: AgentState) -> AgentState:
        """投诉Agent - 处理投诉"""
        customer_id = state.get("customer_id")
        order_id = state.get("order_id")
        message = state.get("customer_message")

        complaint_id = f"CP{str(uuid.uuid4())[:6].upper()}"

        # 使用LLM分析投诉
        complaint_type = "一般投诉"
        sentiment_score = 0

        if self.llm:
            prompt = f"""分析以下客户投诉:

投诉内容: "{message}"

返回JSON格式:
{{
    "complaint_type": "物流投诉|商品质量|服务态度|价格问题|其他",
    "sentiment_score": -10到10的情绪分数,
    "key_issues": ["问题1", "问题2"],
    "suggested_priority": "low|medium|high|urgent",
    "suggested_compensation": "建议的补偿方案"
}}

只返回JSON:"""

            try:
                response = self.llm.invoke([HumanMessage(content=prompt)])
                analysis = json.loads(response.content)
                complaint_type = analysis.get("complaint_type", "一般投诉")
                sentiment_score = analysis.get("sentiment_score", 0)
                priority = analysis.get("suggested_priority", "high")
                llm_analysis = analysis
                llm_used = True
            except:
                llm_analysis = None
                llm_used = False
                priority = "high"
        else:
            llm_analysis = None
            llm_used = False
            priority = "high"
            # 简单规则判断
            if any(w in message for w in ["物流", "快递", "发货"]):
                complaint_type = "物流投诉"
            elif any(w in message for w in ["质量", "坏", "损"]):
                complaint_type = "商品质量"

        complaint_record = {
            "complaint_id": complaint_id,
            "customer_id": customer_id,
            "order_id": order_id,
            "type": complaint_type,
            "content": message,
            "priority": priority,
            "status": "已受理",
            "llm_analysis": llm_analysis,
            "created_at": datetime.now().isoformat()
        }
        complaints_store[complaint_id] = complaint_record

        state["need_escalation"] = True  # 投诉总是需要升级
        state["agent_chain"].append({
            "agent": "complaint",
            "action": "创建投诉工单",
            "message": f"投诉单号: {complaint_id}, 类型: {complaint_type}",
            "llm_used": llm_used,
            "data": complaint_record
        })

        state["current_agent"] = "complaint"
        state["response"] = ""  # 由主管Agent生成最终回复
        return state

    def supervisor_agent(self, state: AgentState) -> AgentState:
        """主管Agent - 审核和最终决策"""

        if self.llm:
            # 使用LLM进行主管审核
            agent_chain_summary = "\n".join(
                f"- {a['agent']}: {a['action']}" for a in state["agent_chain"]
            )

            prompt = f"""你是客服主管。审核以下客服处理流程并生成最终回复。

客户消息: {state['customer_message']}
处理流程:
{agent_chain_summary}

当前响应: {state.get('response', '无')}

请:
1. 审核处理是否合理
2. 如果是投诉，生成安抚性的最终回复
3. 如果需要补偿，给出建议

生成最终回复（友好、专业、有同理心）:"""

            try:
                response = self.llm.invoke([HumanMessage(content=prompt)])

                # 如果之前没有响应，使用主管生成的响应
                if not state.get("response") or state["task_type"] == "complaint":
                    state["response"] = response.content

                llm_used = True
            except:
                if state["task_type"] == "complaint":
                    state["response"] = self._format_complaint_response(state)
                llm_used = False
        else:
            if state["task_type"] == "complaint":
                state["response"] = self._format_complaint_response(state)
            llm_used = False

        state["agent_chain"].append({
            "agent": "supervisor",
            "action": "主管审核通过",
            "message": "已完成审核，工单已升级处理",
            "llm_used": llm_used
        })

        state["current_agent"] = "supervisor"
        return state

    def _format_complaint_response(self, state: AgentState) -> str:
        """格式化投诉响应"""
        complaint_data = None
        for item in state["agent_chain"]:
            if item["agent"] == "complaint" and "data" in item:
                complaint_data = item["data"]
                break

        if complaint_data:
            return f"""🔔 投诉已受理
━━━━━━━━━━━━━━━━
投诉单号: {complaint_data['complaint_id']}
投诉类型: {complaint_data['type']}
优先级: {complaint_data['priority']}
━━━━━━━━━━━━━━━━
我们非常重视您的反馈！
高级客服专员将在2小时内与您联系。

紧急热线: 400-XXX-XXXX"""
        return "您的投诉已受理，我们会尽快处理。"

    def response_generator(self, state: AgentState) -> AgentState:
        """响应生成节点"""
        # 如果还没有响应，生成默认响应
        if not state.get("response"):
            state["response"] = "感谢您的咨询，请问还有什么可以帮助您的吗？"

        state["agent_chain"].append({
            "agent": "response_generator",
            "action": "生成最终响应",
            "message": "工作流完成",
            "llm_used": False
        })

        return state

    async def run(self, message: str, customer_id: str, order_id: str = None) -> Dict[str, Any]:
        """运行工作流"""
        workflow_id = str(uuid.uuid4())[:8]

        initial_state: AgentState = {
            "messages": [],
            "customer_message": message,
            "customer_id": customer_id,
            "order_id": order_id,
            "task_type": "general",
            "current_agent": "",
            "agent_chain": [],
            "response": "",
            "need_escalation": False,
            "workflow_id": workflow_id,
            "error": None
        }

        try:
            if self.graph:
                # 使用 LangGraph 执行工作流
                final_state = self.graph.invoke(initial_state)
            else:
                # 降级模式：顺序执行
                final_state = self.router_agent(initial_state)

                task_type = final_state["task_type"]
                if task_type in ["order_query", "order_status"]:
                    final_state = self.order_agent(final_state)
                elif task_type in ["refund_request", "exchange_request"]:
                    final_state = self.refund_agent(final_state)
                elif task_type == "complaint":
                    final_state = self.complaint_agent(final_state)
                    final_state = self.supervisor_agent(final_state)

                if final_state.get("need_escalation") and task_type != "complaint":
                    final_state = self.supervisor_agent(final_state)

                final_state = self.response_generator(final_state)

            # 保存工作流
            workflows_store[workflow_id] = {
                "workflow_id": workflow_id,
                "task_type": final_state["task_type"],
                "status": "completed",
                "steps": final_state["agent_chain"],
                "created_at": datetime.now().isoformat()
            }

            return {
                "success": True,
                "workflow_id": workflow_id,
                "task_type": final_state["task_type"],
                "status": "completed",
                "response": final_state["response"],
                "agent_chain": final_state["agent_chain"],
                "steps_completed": len(final_state["agent_chain"]),
                "langgraph_used": self.graph is not None,
                "llm_available": self.llm is not None
            }

        except Exception as e:
            return {
                "success": False,
                "workflow_id": workflow_id,
                "error": str(e),
                "response": "抱歉，处理过程中出现错误，请稍后重试。"
            }


# 全局工作流实例
workflow_engine = MultiAgentWorkflow()


# ==================== API 端点 ====================

@router.post("/chat")
async def agent_chat(request: CustomerServiceRequest):
    """
    多Agent协同处理客户请求（基于LangGraph工作流）

    工作流程:
    1. RouterAgent - LLM分析意图并分类
    2. 专业Agent处理（订单/退换货/投诉）
    3. SupervisorAgent - 审核和升级处理
    4. ResponseGenerator - 生成最终响应
    """
    result = await workflow_engine.run(
        message=request.message,
        customer_id=request.customer_id,
        order_id=request.order_id
    )
    return result


@router.get("/workflow/{workflow_id}")
async def get_workflow_detail(workflow_id: str):
    """获取工作流详情"""
    workflow = workflows_store.get(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    return workflow


@router.get("/stats")
async def get_agent_stats():
    """获取Agent系统统计信息"""
    task_type_counts = {}
    llm_usage_count = 0

    for w in workflows_store.values():
        task_type = w.get("task_type", "unknown")
        task_type_counts[task_type] = task_type_counts.get(task_type, 0) + 1

        for step in w.get("steps", []):
            if step.get("llm_used"):
                llm_usage_count += 1

    total = len(workflows_store)

    return {
        "system": "多Agent协同客服系统（LangGraph）",
        "langgraph_available": LANGGRAPH_AVAILABLE,
        "llm_available": workflow_engine.llm is not None,
        "agents": [
            {"role": "router", "name": "路由Agent", "description": "LLM意图分析与任务分发"},
            {"role": "order", "name": "订单Agent", "description": "订单查询与LLM回复生成"},
            {"role": "refund", "name": "退换货Agent", "description": "退换货处理与审批"},
            {"role": "complaint", "name": "投诉Agent", "description": "投诉分析与工单创建"},
            {"role": "supervisor", "name": "主管Agent", "description": "LLM审核与最终决策"}
        ],
        "statistics": {
            "total_workflows": total,
            "completed": total,
            "llm_calls": llm_usage_count,
            "task_type_distribution": task_type_counts
        }
    }


@router.get("/orders")
async def get_all_orders():
    """获取所有订单"""
    return {"orders": list(MOCK_ORDERS.values()), "total": len(MOCK_ORDERS)}


@router.get("/orders/{order_id}")
async def get_order(order_id: str):
    """获取订单详情"""
    order = MOCK_ORDERS.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    return order


@router.get("/customers")
async def get_all_customers():
    """获取所有客户"""
    return {"customers": list(MOCK_CUSTOMERS.values()), "total": len(MOCK_CUSTOMERS)}


@router.get("/customers/{customer_id}")
async def get_customer(customer_id: str):
    """获取客户详情"""
    customer = MOCK_CUSTOMERS.get(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")
    orders = [o for o in MOCK_ORDERS.values() if o["customer_id"] == customer_id]
    return {"customer": customer, "orders": orders, "order_count": len(orders)}

