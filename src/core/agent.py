"""
LangChain Agent - 多任务问答核心逻辑（支持 OpenAI）
"""
import asyncio
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from tools.tool_manager import ToolManager
from schemas.models import TaskType, ToolCall

# 尝试导入 OpenAI（新版本）
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ OpenAI 库未安装")


class MultiTaskAgent:
    """多任务AI Agent - 支持 LLM 驱动"""

    def __init__(self, tool_manager: ToolManager, use_llm: bool = True):
        self.tool_manager = tool_manager
        self.conversation_history = []
        self.use_llm = use_llm and OPENAI_AVAILABLE
        self.client = None

        # 初始化 OpenAI 客户端
        if self.use_llm:
            api_key = os.getenv("OPENAI_API_KEY")
            api_base = os.getenv("OPENAI_API_BASE")

            if api_key:
                try:
                    self.client = OpenAI(
                        api_key=api_key,
                        base_url=api_base if api_base else "https://api.openai.com/v1"
                    )
                    # 测试连接
                    print(f"✓ OpenAI 客户端初始化成功 (base_url: {api_base or 'default'})")
                    self.use_llm = True
                except Exception as e:
                    print(f"⚠️ OpenAI 客户端初始化失败: {e}")
                    self.use_llm = False
            else:
                print("⚠️ OPENAI_API_KEY 未配置，将使用规则引擎")
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

            # 确保返回字符串
            if hasattr(response, 'choices') and response.choices:
                content = response.choices[0].message.content
                return str(content) if content else ""
            else:
                # 如果响应格式不对，尝试转换
                return str(response)
        except Exception as e:
            print(f"❌ LLM API 调用错误: {e}")
            raise

    def _classify_task_with_llm(self, query: str) -> TaskType:
        """使用 LLM 分类任务"""
        if not self.use_llm:
            return self._classify_task_rule_based(query)

        try:
            messages = [
                {"role": "system", "content": "你是一个问答分类专家。根据用户查询，将其分类为以下之一：WEATHER、NEWS、SEARCH或QA。只返回一个单词。"},
                {"role": "user", "content": f"分类: {query}"}
            ]

            response = self._call_llm(messages, temperature=0.3)

            if not response or not isinstance(response, str):
                print(f"⚠️ LLM 返回无效响应: {type(response)}")
                return self._classify_task_rule_based(query)

            classification = response.strip().upper()

            # 映射 LLM 输出到 TaskType
            mapping = {
                "WEATHER": TaskType.WEATHER,
                "NEWS": TaskType.NEWS,
                "SEARCH": TaskType.SEARCH,
                "QA": TaskType.QA
            }
            return mapping.get(classification, TaskType.QA)
        except Exception as e:
            print(f"⚠️ LLM 分类失败: {e}，使用规则引擎")
            return self._classify_task_rule_based(query)

    def _classify_task_rule_based(self, query: str) -> TaskType:
        """基于规则的任务分类"""
        query_lower = query.lower()

        if any(word in query_lower for word in ["天气", "weather", "温度", "下雨", "气温"]):
            return TaskType.WEATHER
        elif any(word in query_lower for word in ["新闻", "news", "科技", "最近发生"]):
            return TaskType.NEWS
        elif any(word in query_lower for word in ["搜索", "查询", "search", "find"]):
            return TaskType.SEARCH
        else:
            return TaskType.QA

    def _generate_tool_calls_with_llm(self, query: str, task_type: TaskType) -> List[Dict[str, Any]]:
        """使用 LLM 生成工具调用参数 - 使用规则引擎"""
        # 由于 LLM 返回格式难以预测，直接使用规则引擎
        # 这样更稳定、快速、可靠
        return self._generate_tool_calls_rule_based(query, task_type)

    def _generate_tool_calls_rule_based(self, query: str, task_type: TaskType) -> List[Dict[str, Any]]:
        """基于规则生成工具调用"""
        tool_calls = []

        if task_type == TaskType.WEATHER:
            cities = ["北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "南京"]
            city = "北京"
            for c in cities:
                if c in query:
                    city = c
                    break

            tool_calls.append({
                "tool": "weather",
                "params": {"city": city}
            })

        elif task_type == TaskType.NEWS:
            tool_calls.append({
                "tool": "news",
                "params": {"category": "tech", "limit": 3}
            })

        elif task_type == TaskType.SEARCH:
            search_query = query.replace("搜索", "").replace("查询", "").strip()
            tool_calls.append({
                "tool": "search",
                "params": {"query": search_query}
            })

        return tool_calls

    def _generate_response_with_llm(self, query: str, tool_results: List[Dict[str, Any]]) -> str:
        """使用 LLM 润色工具返回的真实数据"""
        if not tool_results:
            # 没有工具结果时，直接用 LLM 回答
            if self.use_llm:
                try:
                    messages = [
                        {"role": "system", "content": """你是一个专业、温暖且贴心的AI助手。请遵循以下回复原则：

1. 避免使用模板化语言如"感谢您的咨询，还有什么可以帮助您的吗？"
2. 根据用户问题类型调整语气：
   - 紧急问题：快速响应，提供明确解决方案
   - 困惑问题：详细解释，保持耐心
   - 投诉问题：表达理解和歉意，提供具体帮助
3. 提供价值增值：在基本回答基础上，主动提供相关的有用信息或建议
4. 自然过渡：使用自然的语言引导到下一步，如"需要我为您..."、"如果您还想知道..."
5. 保持真诚：用真实的语气表达关心和帮助的意愿
6. 长度适中：回复既充分又简洁，避免过于简短或冗长

请用温暖、专业、真诚的中文回答用户问题。"""},
                        {"role": "user", "content": query}
                    ]
                    return self._call_llm(messages, temperature=0.7)
                except Exception as e:
                    print(f"⚠️ LLM 回答失败: {e}")
                    pass
            return f"抱歉，我无法处理您的查询: {query}"

        # 有工具结果时，用 LLM 润色真实数据
        if not self.use_llm:
            return self._generate_response_rule_based(query, tool_results)

        try:
            # 构建包含真实数据的 prompt
            data_str = self._format_tool_results_for_llm(tool_results)

            messages = [
                {"role": "system", "content": """你是一个专业、贴心的AI助手。基于用户问题和提供的数据，请生成温暖、有用且个性化的回复。

回复时请：
1. 直接使用数据回答用户问题，不要提及"根据数据"等字眼
2. 提供实用的建议或相关的额外信息
3. 如果是天气信息，给出穿衣建议或活动提醒
4. 如果是新闻信息，突出重点或提供背景说明
5. 如果是搜索结果，总结要点或提供进一步查询建议
6. 用自然的语气表达，避免生硬和模板化
7. 最后可以主动询问是否需要其他相关帮助

目标：让用户感受到真诚的关心和专业的服务。"""},
                {"role": "user", "content": f"用户问题：{query}\n\n数据来源：\n{data_str}"}
            ]

            response = self._call_llm(messages, temperature=0.5)
            return response if response else self._generate_response_rule_based(query, tool_results)
        except Exception as e:
            print(f"⚠️ LLM 润色失败: {e}，使用规则引擎")
            return self._generate_response_rule_based(query, tool_results)

    def _format_tool_results_for_llm(self, tool_results: List[Dict[str, Any]]) -> str:
        """将工具结果格式化为 LLM 可读的文本"""
        formatted_parts = []

        for result in tool_results:
            tool_name = result.get("tool", "unknown")
            source = result.get("source", "unknown")

            if tool_name == "weather":
                city = result.get("city", "未知")
                data = result.get("data", {})
                formatted_parts.append(
                    f"【天气数据 - 来源: {source}】\n"
                    f"城市: {city}\n"
                    f"温度: {data.get('temp', '未知')}°C\n"
                    f"体感温度: {data.get('feels_like', '未知')}°C\n"
                    f"天气状况: {data.get('condition', '未知')}\n"
                    f"湿度: {data.get('humidity', '未知')}%\n"
                    f"风速: {data.get('wind_speed', '未知')} km/h\n"
                    f"能见度: {data.get('visibility', '未知')} km"
                )

            elif tool_name == "news":
                category = result.get("category", "未知")
                news_list = result.get("news", [])
                news_text = f"【新闻数据 - 来源: {source}，分类: {category}】\n"
                for i, news in enumerate(news_list, 1):
                    news_text += f"{i}. 标题: {news.get('title', '无标题')}\n"
                    if news.get('summary'):
                        news_text += f"   摘要: {news.get('summary')}\n"
                    if news.get('date'):
                        news_text += f"   日期: {news.get('date')}\n"
                formatted_parts.append(news_text)

            elif tool_name == "search":
                search_query = result.get("query", "")
                results = result.get("results", [])
                search_text = f"【搜索结果 - 来源: {source}，关键词: {search_query}】\n"
                for i, item in enumerate(results, 1):
                    search_text += f"{i}. {item.get('title', '无标题')}\n"
                    if item.get('snippet'):
                        search_text += f"   {item.get('snippet')}\n"
                formatted_parts.append(search_text)

            else:
                # 其他工具，直接序列化
                formatted_parts.append(f"【{tool_name}结果】\n{json.dumps(result, ensure_ascii=False, indent=2)}")

        return "\n\n".join(formatted_parts)

    def _generate_response_rule_based(self, query: str, tool_results: List[Dict[str, Any]]) -> str:
        """基于规则生成响应（备用方案） - 人性化版本"""
        if not tool_results:
            return f"抱歉，我现在无法处理您的查询。让我换个方式为您服务，或者您可以尝试重新描述一下需求。"

        first_result = tool_results[0] if tool_results else {}

        if "error" in first_result:
            return f"抱歉，处理过程中遇到了一些问题：{first_result['error']}。让我尝试其他方式来帮助您。"

        tool_name = first_result.get("tool", "")
        source = first_result.get("source", "unknown")

        if tool_name == "weather":
            data = first_result.get("data", {})
            city = first_result.get("city", "")
            temp = data.get('temp', 'N/A')
            condition = data.get('condition', 'N/A')
            humidity = data.get('humidity', 'N/A')

            # 人性化的天气回复
            response = f"📍 {city}今天的天气情况：\n"
            response += f"  🌡️ 当前温度 {temp}°C，{condition}\n"
            response += f"  💧 湿度 {humidity}%\n"

            # 添加实用建议
            if temp != 'N/A':
                if float(temp) < 10:
                    response += f"\n💡 温度较低，建议您多穿一件外套保暖。"
                elif float(temp) > 28:
                    response += f"\n💡 天气较热，注意防暑降温，多补充水分。"
                else:
                    response += f"\n💡 温度适宜，很适合外出活动呢。"

            if data.get('wind_speed'):
                response += f"\n🌬️ 风速 {data.get('wind_speed')} km/h，户外活动时请注意防风。"

            response += f"\n\n需要我为您查询其他城市的天气情况吗？"
            return response

        elif tool_name == "news":
            news_list = first_result.get("news", [])
            if not news_list:
                return f"抱歉，暂时没有找到相关的新闻信息。需要我为您搜索其他内容吗？"

            response = f"📰 为您找到了以下最新动态：\n"
            for i, news in enumerate(news_list, 1):
                response += f"\n{i}. {news.get('title', '无标题')}\n"
                if news.get('summary'):
                    response += f"   💭 {news.get('summary')[:120]}...\n"
                if news.get('date'):
                    response += f"   📅 {news.get('date')}\n"

            response += f"\n这些信息中有您特别感兴趣的吗？我可以为您深入了解某个话题。"
            return response

        elif tool_name == "search":
            results = first_result.get("results", [])
            search_query = first_result.get("query", "")
            if not results:
                return f"抱歉，关于「{search_query}」没有找到相关信息。让我换个关键词为您搜索，或者您可以提供更多细节？"

            response = f"🔍 关于「{search_query}」为您找到了：\n"
            for i, result in enumerate(results, 1):
                response += f"\n{i}. {result.get('title', '无标题')}\n"
                if result.get('snippet'):
                    response += f"   📝 {result.get('snippet')[:150]}...\n"

            response += f"\n这些结果中有您想了解更多的吗？我可以为您提供更详细的信息。"
            return response

        else:
            return f"我已经为您处理了查询，得到了一些信息。让我用更好的方式为您整理一下，请稍等..."

    async def process_query(self, query: str) -> Dict[str, Any]:
        """处理用户查询"""
        # 分类任务（使用 LLM 或规则）
        task_type = self._classify_task_with_llm(query)

        # 生成工具调用（使用 LLM 或规则）
        tool_calls_config = self._generate_tool_calls_with_llm(query, task_type)

        # 并行执行工具
        tool_results = []
        if tool_calls_config:
            tool_results = await self.tool_manager.execute_tools_parallel(tool_calls_config)

        # 生成响应（使用 LLM 或规则）
        response_text = self._generate_response_with_llm(query, tool_results)

        # 记录工具调用
        tool_calls = [
            ToolCall(
                tool_name=result.get("tool", "unknown"),
                parameters=tool_calls_config[i].get("params", {}) if i < len(tool_calls_config) else {},
                result=json.dumps(result, ensure_ascii=False)
            )
            for i, result in enumerate(tool_results)
        ]

        return {
            "response": response_text,
            "task_type": task_type.value,
            "tool_calls": tool_calls,
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "llm_used": self.use_llm
        }

    def add_to_history(self, role: str, content: str, tool_calls: List[ToolCall] = None):
        """添加对话历史"""
        from schemas.models import Message

        message = Message(
            role=role,
            content=content,
            tool_calls=tool_calls or []
        )
        self.conversation_history.append(message)

    def get_history(self) -> List[Dict[str, Any]]:
        """获取对话历史"""
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
            }
            for msg in self.conversation_history
        ]

    def clear_history(self):
        """清空对话历史"""
        self.conversation_history = []
