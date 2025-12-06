"""
智能客服中心专用Agent
"""
import asyncio
import json
import re
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from tools.customer_service_tools import (
    execute_customer_service_tool, CUSTOMER_SERVICE_TOOLS
)
from schemas.customer_service_models import (
    CustomerServiceTaskType, TicketCategory, TicketPriority,
    TicketStatus, ChannelType
)

# 尝试导入 OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class CustomerServiceAgent:
    """智能客服中心Agent"""

    def __init__(self, use_llm: bool = True):
        self.use_llm = use_llm and OPENAI_AVAILABLE
        self.client = None

        # 初始化 OpenAI 客户端
        if self.use_llm:
            try:
                api_key = os.getenv("OPENAI_API_KEY")
                api_base = os.getenv("OPENAI_API_BASE")

                if api_key:
                    self.client = OpenAI(
                        api_key=api_key,
                        base_url=api_base if api_base else "https://api.openai.com/v1"
                    )
                    print("✓ 客服中心OpenAI客户端初始化成功")
                    self.use_llm = True
                else:
                    print("⚠️ OPENAI_API_KEY 未配置，将使用规则引擎")
                    self.use_llm = False
            except Exception as e:
                print(f"⚠️ OpenAI 客户端初始化失败: {e}")
                self.use_llm = False

    def _call_llm(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
        """调用 OpenAI API"""
        if not self.client:
            raise Exception("OpenAI 客户端未初始化")

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=temperature,
                max_tokens=1000
            )

            if hasattr(response, 'choices') and response.choices:
                content = response.choices[0].message.content
                return str(content) if content else ""
            else:
                return str(response)
        except Exception as e:
            print(f"❌ LLM API 调用错误: {e}")
            raise

    async def classify_customer_service_query(self, query: str) -> CustomerServiceTaskType:
        """分类客服查询类型"""
        if self.use_llm:
            return await self._classify_with_llm(query)
        else:
            return self._classify_with_rules(query)

    async def _classify_with_llm(self, query: str) -> CustomerServiceTaskType:
        """使用LLM分类客服查询"""
        try:
            messages = [
                {"role": "system", "content": """你是一个客服查询分类专家。根据用户的查询，将其分类为以下类型之一：
- order_query: 订单查询
- order_modify: 订单修改
- order_cancel: 订单取消
- refund_request: 退款申请
- return_exchange: 退换货
- logistics_tracking: 物流查询
- product_info: 产品信息
- tech_support: 技术支持
- complaint_handling: 投诉处理
- account_issues: 账户问题
- payment_issues: 支付问题
- consultation: 咨询服务
- escalation: 问题升级

只返回分类结果，不要其他解释。"""},
                {"role": "user", "content": f"分类客服查询: {query}"}
            ]

            response = self._call_llm(messages, temperature=0.3)
            classification = response.strip().lower()

            # 映射到枚举值
            mapping = {
                "order_query": CustomerServiceTaskType.ORDER_QUERY,
                "order_modify": CustomerServiceTaskType.ORDER_MODIFY,
                "order_cancel": CustomerServiceTaskType.ORDER_CANCEL,
                "refund_request": CustomerServiceTaskType.REFUND_REQUEST,
                "return_exchange": CustomerServiceTaskType.RETURN_EXCHANGE,
                "logistics_tracking": CustomerServiceTaskType.LOGISTICS_TRACKING,
                "product_info": CustomerServiceTaskType.PRODUCT_INFO,
                "tech_support": CustomerServiceTaskType.TECHNICAL_SUPPORT,
                "complaint_handling": CustomerServiceTaskType.COMPLAINT_HANDLING,
                "account_issues": CustomerServiceTaskType.ACCOUNT_ISSUES,
                "payment_issues": CustomerServiceTaskType.PAYMENT_ISSUES,
                "consultation": CustomerServiceTaskType.CONSULTATION,
                "escalation": CustomerServiceTaskType.ESCALATION
            }

            return mapping.get(classification, CustomerServiceTaskType.CONSULTATION)

        except Exception as e:
            print(f"⚠️ LLM 分类失败: {e}，使用规则引擎")
            return self._classify_with_rules(query)

    def _classify_with_rules(self, query: str) -> CustomerServiceTaskType:
        """使用规则分类客服查询"""
        query_lower = query.lower()

        # 订单相关
        if any(word in query_lower for word in ["订单", "order", "购买", "下单", "订单号"]):
            if any(word in query_lower for word in ["查", "查询", "看", "状态"]):
                return CustomerServiceTaskType.ORDER_QUERY
            elif any(word in query_lower for word in ["修改", "改", "更改", "地址"]):
                return CustomerServiceTaskType.ORDER_MODIFY
            elif any(word in query_lower for word in ["取消", "退单", "不要"]):
                return CustomerServiceTaskType.ORDER_CANCEL

        # 退换货相关
        elif any(word in query_lower for word in ["退款", "退钱", "refund", "退货"]):
            return CustomerServiceTaskType.REFUND_REQUEST
        elif any(word in query_lower for word in ["换货", "exchange", "换一个"]):
            return CustomerServiceTaskType.RETURN_EXCHANGE

        # 物流相关
        elif any(word in query_lower for word in ["物流", "快递", "配送", "送货", "tracking"]):
            return CustomerServiceTaskType.LOGISTICS_TRACKING

        # 产品相关
        elif any(word in query_lower for word in ["产品", "商品", "规格", "参数", "功能"]):
            return CustomerServiceTaskType.PRODUCT_INFO

        # 技术支持
        elif any(word in query_lower for word in ["故障", "坏了", "不能", "无法", "技术"]):
            return CustomerServiceTaskType.TECHNICAL_SUPPORT

        # 投诉相关
        elif any(word in query_lower for word in ["投诉", "举报", "不满", "差评", "投诉"]):
            return CustomerServiceTaskType.COMPLAINT_HANDLING

        # 账户相关
        elif any(word in query_lower for word in ["账户", "账号", "密码", "登录", "注册"]):
            return CustomerServiceTaskType.ACCOUNT_ISSUES

        # 支付相关
        elif any(word in query_lower for word in ["支付", "付款", "扣款", "收费", "payment"]):
            return CustomerServiceTaskType.PAYMENT_ISSUES

        # 升级相关
        elif any(word in query_lower for word in ["升级", "经理", "主管", "投诉", "媒体"]):
            return CustomerServiceTaskType.ESCALATION

        else:
            return CustomerServiceTaskType.CONSULTATION

    async def generate_tool_calls(self, query: str, task_type: CustomerServiceTaskType) -> List[Dict[str, Any]]:
        """生成工具调用"""
        tool_calls = []

        # 根据任务类型生成相应的工具调用
        if task_type == CustomerServiceTaskType.ORDER_QUERY:
            # 提取订单号
            order_id = self._extract_order_id(query)
            if order_id:
                tool_calls.append({
                    "tool": "order_query",
                    "params": {"order_id": order_id}
                })

            # 提取客户信息
            customer_info = self._extract_customer_info(query)
            if customer_info:
                tool_calls.append({
                    "tool": "customer_lookup",
                    "params": customer_info
                })

        elif task_type == CustomerServiceTaskType.LOGISTICS_TRACKING:
            # 提取快递单号
            tracking_number = self._extract_tracking_number(query)
            if tracking_number:
                tool_calls.append({
                    "tool": "logistics_tracking",
                    "params": {"tracking_number": tracking_number}
                })

            # 如果没有快递单号，尝试用订单号
            else:
                order_id = self._extract_order_id(query)
                if order_id:
                    tool_calls.append({
                        "tool": "logistics_tracking",
                        "params": {"order_id": order_id}
                    })

        elif task_type == CustomerServiceTaskType.REFUND_REQUEST:
            order_id = self._extract_order_id(query)
            customer_info = self._extract_customer_info(query)

            if order_id and customer_info:
                tool_calls.append({
                    "tool": "refund_process",
                    "params": {
                        "order_id": order_id,
                        "customer_id": customer_info.get("customer_id"),
                        "refund_reason": self._extract_refund_reason(query),
                        "refund_type": "full"
                    }
                })

        elif task_type in [CustomerServiceTaskType.COMPLAINT_HANDLING, CustomerServiceTaskType.ESCALATION]:
            # 投诉或升级，创建工单
            customer_info = self._extract_customer_info(query)
            if customer_info:
                tool_calls.append({
                    "tool": "ticket_create",
                    "params": {
                        "customer_id": customer_info.get("customer_id"),
                        "title": self._extract_title(query),
                        "description": query,
                        "category": "complaint" if task_type == CustomerServiceTaskType.COMPLAINT_HANDLING else "escalation",
                        "priority": "high" if task_type == CustomerServiceTaskType.ESCALATION else "medium"
                    }
                })

        # 对于所有查询，搜索相关知识库
        keywords = self._extract_keywords(query)
        if keywords:
            tool_calls.append({
                "tool": "knowledge_search",
                "params": {
                    "query": keywords,
                    "limit": 3
                }
            })

        return tool_calls

    def _extract_order_id(self, text: str) -> Optional[str]:
        """提取订单号"""
        # 匹配各种订单号格式
        patterns = [
            r'ORD\d{6,}',      # ORD123456
            r'\d{10,}',        # 长数字
            r'[A-Z]{2,}\d{6,}', # 字母+数字
            r'订单[号]?[：:]?\s*([A-Z0-9]+)', # 订单号：XXX
        ]

        for pattern in patterns:
            match = re.search(pattern, text.upper())
            if match:
                return match.group(1) if match.groups() else match.group(0)
        return None

    def _extract_tracking_number(self, text: str) -> Optional[str]:
        """提取快递单号"""
        patterns = [
            r'SF\d{10}',       # 顺丰
            r'YT\d{10}',       # 圆通
            r'ZT\d{10}',       # 中通
            r'YD\d{10}',       # 韵达
            r'\d{12,}',        # 长数字序列
            r'快递[单号]?[：:]?\s*([A-Z0-9]+)', # 快递单号：XXX
        ]

        for pattern in patterns:
            match = re.search(pattern, text.upper())
            if match:
                return match.group(1) if match.groups() else match.group(0)
        return None

    def _extract_customer_info(self, text: str) -> Optional[Dict[str, Any]]:
        """提取客户信息"""
        info = {}

        # 提取手机号
        phone_pattern = r'1[3-9]\d{9}'
        phone_match = re.search(phone_pattern, text)
        if phone_match:
            info["phone"] = phone_match.group(0)

        # 提取邮箱
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, text)
        if email_match:
            info["email"] = email_match.group(0)

        # 提取姓名（简单匹配）
        name_patterns = [
            r'我叫([^，。！？\s]+)',
            r'我是([^，。！？\s]+)',
            r'姓名[是]?[：:]?\s*([^，。！？\s]+)'
        ]

        for pattern in name_patterns:
            match = re.search(pattern, text)
            if match:
                info["name"] = match.group(1)
                break

        return info if info else None

    def _extract_refund_reason(self, text: str) -> str:
        """提取退款原因"""
        reasons = {
            "质量问题": ["质量问题", "坏了", "损坏", "有缺陷", "不好用"],
            "尺寸不合适": ["尺寸", "大小", "不合适", "太大", "太小"],
            "个人原因": ["不想要了", "买错了", "不要了", "个人原因"],
            "商品损坏": ["收到就坏了", "运输损坏", "包装破损"],
            "描述不符": ["和描述不符", "不是我要的", "颜色不对", "型号不对"]
        }

        text_lower = text.lower()
        for reason, keywords in reasons.items():
            if any(keyword in text_lower for keyword in keywords):
                return reason

        return "其他原因"

    def _extract_title(self, text: str) -> str:
        """提取工单标题"""
        # 取前50个字符作为标题
        title = text[:50]
        if len(text) > 50:
            title += "..."
        return title

    def _extract_keywords(self, text: str) -> str:
        """提取关键词"""
        # 简单的关键词提取
        keywords = []

        # 常见关键词
        common_keywords = [
            "订单", "退款", "退货", "物流", "快递", "配送",
            "产品", "质量", "故障", "账户", "支付", "投诉"
        ]

        for keyword in common_keywords:
            if keyword in text:
                keywords.append(keyword)

        return " ".join(keywords) if keywords else text[:20]

    async def generate_response(self, query: str, tool_results: List[Dict[str, Any]], task_type: CustomerServiceTaskType) -> str:
        """生成客服回复"""
        if not tool_results:
            return await self._generate_general_response(query, task_type)

        if self.use_llm:
            return await self._generate_llm_response(query, tool_results, task_type)
        else:
            return self._generate_rule_response(query, tool_results, task_type)

    async def _generate_general_response(self, query: str, task_type: CustomerServiceTaskType) -> str:
        """生成通用回复（无工具结果时）"""
        if not self.use_llm:
            return f"您好，我理解您的需求。关于{task_type.value}，我需要更多信息来帮助您。请提供相关的订单号或联系方式。"

        try:
            messages = [
                {"role": "system", "content": """你是一个专业的客服代表。请用温暖、专业、贴心的语调回复客户。

回复原则：
1. 表达理解和关心
2. 主动询问必要信息
3. 提供初步建议或解决方案
4. 避免模板化语言
5. 保持积极正向的态度

请直接回复客户，不要提及"作为AI助手"等字样。"""},
                {"role": "user", "content": f"客户咨询：{query}\n问题类型：{task_type.value}"}
            ]

            response = self._call_llm(messages, temperature=0.7)
            return response if response else "您好，我理解您的情况。为了更好地帮助您，请提供更多详细信息。"

        except Exception as e:
            print(f"⚠️ LLM 回复生成失败: {e}")
            return "您好，我理解您的需求。为了更好地协助您，请提供相关的订单号或联系方式。"

    async def _generate_llm_response(self, query: str, tool_results: List[Dict[str, Any]], task_type: CustomerServiceTaskType) -> str:
        """使用LLM生成回复"""
        try:
            # 整理工具结果
            tool_summary = self._format_tool_results_for_llm(tool_results)

            messages = [
                {"role": "system", "content": f"""你是一个专业的客服代表。基于客户问题和查询到的信息，请生成温暖、专业、有用的回复。

回复要求：
1. 基于查询到的真实信息回答客户问题
2. 表达理解和关心
3. 提供具体的解决方案或下一步建议
4. 询问是否需要其他帮助
5. 用自然、亲切的语调，避免生硬的模板化语言

当前问题类型：{task_type.value}"""},
                {"role": "user", "content": f"客户问题：{query}\n\n查询到的信息：\n{tool_summary}"}
            ]

            response = self._call_llm(messages, temperature=0.6)
            return response if response else self._generate_rule_response(query, tool_results, task_type)

        except Exception as e:
            print(f"⚠️ LLM 回复生成失败: {e}")
            return self._generate_rule_response(query, tool_results, task_type)

    def _generate_rule_response(self, query: str, tool_results: List[Dict[str, Any]], task_type: CustomerServiceTaskType) -> str:
        """使用规则生成回复"""
        responses = []

        for result in tool_results:
            tool_name = result.get("tool")

            if tool_name == "order_query" and result.get("success"):
                order = result.get("order", {})
                status_desc = order.get("status_description", "未知状态")
                responses.append(f"您的订单 {order.get('order_id')} 当前状态是：{status_desc}")

            elif tool_name == "logistics_tracking" and result.get("success"):
                logistics = result.get("logistics", {})
                status_desc = logistics.get("status_description", "未知状态")
                current_loc = logistics.get("current_location", "未知位置")
                responses.append(f"您的物流状态是：{status_desc}，当前位置：{current_loc}")

            elif tool_name == "refund_process" and result.get("success"):
                refund_id = result.get("refund_id")
                processing_time = result.get("processing_time")
                responses.append(f"您的退款申请已提交（编号：{refund_id}），预计{processing_time}内完成")

            elif tool_name == "customer_lookup" and result.get("success"):
                customer = result.get("customer", {})
                name = customer.get("name", "客户")
                level = customer.get("member_level", "普通")
                responses.append(f"您好{name}（{level}会员），很高兴为您服务")

            elif tool_name == "knowledge_search" and result.get("success"):
                results = result.get("results", [])
                if results:
                    top_result = results[0]
                    responses.append(f"相关知识：{top_result.get('title', '')} - {top_result.get('content', '')[:100]}...")

            elif tool_name == "ticket_create" and result.get("success"):
                ticket_id = result.get("ticket_id")
                responses.append(f"您的问题已创建工单（编号：{ticket_id}），我们会尽快处理")

        if not responses:
            return "您好，我理解您的需求。为了更好地帮助您，请提供相关的订单号或具体问题描述。"

        # 组合回复
        base_response = " ".join(responses)

        # 添加结束语
        endings = [
            "还有什么其他问题可以帮助您吗？",
            "如果您需要更多信息，请随时告诉我。",
            "希望这些信息对您有帮助！",
            "如果问题没有解决，我可以为您继续查询。"
        ]

        import random
        ending = random.choice(endings)

        return f"{base_response} {ending}"

    def _format_tool_results_for_llm(self, tool_results: List[Dict[str, Any]]) -> str:
        """格式化工具结果供LLM使用"""
        formatted_parts = []

        for result in tool_results:
            tool_name = result.get("tool", "unknown")

            if tool_name == "order_query" and result.get("success"):
                order = result.get("order", {})
                formatted_parts.append(
                    f"订单信息：订单号{order.get('order_id')}，状态{order.get('status_description')}，"
                    f"金额{order.get('total_amount')}元，预计送达{order.get('estimated_delivery')}"
                )

            elif tool_name == "logistics_tracking" and result.get("success"):
                logistics = result.get("logistics", {})
                history = logistics.get("tracking_history", [])
                latest_update = history[-1] if history else {}
                formatted_parts.append(
                    f"物流信息：{logistics.get('logistics_company')}，单号{logistics.get('tracking_number')}，"
                    f"状态{logistics.get('status_description')}，"
                    f"最新更新：{latest_update.get('time', '')} {latest_update.get('location', '')}"
                )

            elif tool_name == "customer_lookup" and result.get("success"):
                customer = result.get("customer", {})
                formatted_parts.append(
                    f"客户信息：{customer.get('name')}，{customer.get('member_level')}会员，"
                    f"历史订单{customer.get('total_orders')}个，满意度{customer.get('satisfaction_score')}分"
                )

            elif tool_name == "refund_process" and result.get("success"):
                formatted_parts.append(
                    f"退款信息：退款编号{result.get('refund_id')}，金额{result.get('refund_amount')}元，"
                    f"预计{result.get('processing_time')}完成"
                )

            elif tool_name == "ticket_create" and result.get("success"):
                formatted_parts.append(
                    f"工单信息：工单号{result.get('ticket_id')}，分类{result.get('category')}，"
                    f"优先级{result.get('priority')}，预计{result.get('estimated_resolution')}解决"
                )

            elif tool_name == "knowledge_search" and result.get("success"):
                results = result.get("results", [])
                if results:
                    knowledge_parts = []
                    for i, item in enumerate(results[:3], 1):
                        knowledge_parts.append(f"{i}. {item.get('title', '')}: {item.get('content', '')[:100]}...")
                    formatted_parts.append(f"相关知识库：\n" + "\n".join(knowledge_parts))

        return "\n\n".join(formatted_parts)

    async def process_customer_service_query(self, query: str) -> Dict[str, Any]:
        """处理客服��询的主流程"""
        # 1. 分类查询类型
        task_type = await self.classify_customer_service_query(query)

        # 2. 生成工具调用
        tool_calls_config = await self.generate_tool_calls(query, task_type)

        # 3. 并行执行工具
        tool_results = []
        if tool_calls_config:
            tasks = []
            for tool_config in tool_calls_config:
                task = execute_customer_service_tool(
                    tool_config["tool"],
                    tool_config["params"]
                )
                tasks.append(task)

            tool_results = await asyncio.gather(*tasks, return_exceptions=True)
            # 过滤异常结果
            tool_results = [r for r in tool_results if isinstance(r, dict)]

        # 4. 生成回复
        response_text = await self.generate_response(query, tool_results, task_type)

        # 5. 返回结果
        return {
            "response": response_text,
            "task_type": task_type.value,
            "tool_calls": tool_calls_config,
            "tool_results": tool_results,
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "agent_type": "customer_service",
            "llm_used": self.use_llm
        }