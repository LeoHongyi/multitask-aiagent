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

        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=temperature,
            max_tokens=1000
        )
        return response.choices[0].message.content

    def _classify_task_with_llm(self, query: str) -> TaskType:
        """使用 LLM 分类任务"""
        if not self.use_llm:
            return self._classify_task_rule_based(query)

        try:
            messages = [
                {"role": "system", "content": "你是一个问答分类专家。根据用户查询，将其分类为以下之一：WEATHER（天气查询）、NEWS（新闻查询）、SEARCH（搜索查询）或 QA（通用问答）。只返回分类名称，不要其他内容。"},
                {"role": "user", "content": f"请分类这个查询：{query}"}
            ]

            response = self._call_llm(messages, temperature=0.3)
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
        """使用 LLM 生成工具调用参数"""
        if not self.use_llm:
            return self._generate_tool_calls_rule_based(query, task_type)

        try:
            tools_info = self.tool_manager.get_tool_descriptions()

            system_prompt = (
                "你是一个智能助手。根据用户查询和可用工具，生成需要调用的工具和参数。\n\n"
                f"可用工具：\n"
                f"- weather: 查询天气，参数 city (城市名)\n"
                f"- news: 获取新闻，参数 category (分类), limit (数量)\n"
                f"- search: 搜索信息，参数 query (搜索词)\n"
                f"- text_process: 文本处理，参数 text, action\n\n"
                '只返回 JSON 数组，格式: [{"tool": "工具名", "params": {"参数名": "值"}}]\n'
                '例如: [{"tool": "weather", "params": {"city": "北京"}}]\n'
                '不要返回任何其他文字，只返回 JSON。'
            )

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ]

            response = self._call_llm(messages, temperature=0.1)

            # 清理并解析 JSON
            response_clean = response.strip()

            # 移除可能的 markdown 代码块
            if "```json" in response_clean:
                response_clean = response_clean.split("```json")[1].split("```")[0].strip()
            elif "```" in response_clean:
                response_clean = response_clean.split("```")[1].split("```")[0].strip()

            # 尝试找到 JSON 数组
            start_idx = response_clean.find('[')
            end_idx = response_clean.rfind(']')
            if start_idx != -1 and end_idx != -1:
                response_clean = response_clean[start_idx:end_idx + 1]

            if not response_clean:
                print(f"⚠️ LLM 返回空内容，使用规则引擎")
                return self._generate_tool_calls_rule_based(query, task_type)

            tool_calls = json.loads(response_clean)
            return tool_calls if isinstance(tool_calls, list) else []
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON 解析失败: {e}，LLM 返回: {response[:100] if 'response' in dir() else 'N/A'}")
            return self._generate_tool_calls_rule_based(query, task_type)
        except Exception as e:
            print(f"⚠️ LLM 生成工具调用失败: {e}，使用规则引擎")
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
                        {"role": "system", "content": "你是一个有用的问答助手，用简洁的中文回答问题。"},
                        {"role": "user", "content": query}
                    ]
                    return self._call_llm(messages, temperature=0.7)
                except:
                    pass
            return f"抱歉，我无法处理您的查询: {query}"

        # 有工具结果时，用 LLM 润色真实数据
        if not self.use_llm:
            return self._generate_response_rule_based(query, tool_results)

        try:
            # 构建包含真实数据的 prompt
            system_prompt = (
                "你是一个智能助手。请根据以下【真实数据】回答用户问题。\n"
                "要求：\n"
                "1. 必须基于提供的真实数据回答，不要编造任何信息\n"
                "2. 用自然流畅的中文表达\n"
                "3. 如果数据来源是 'fallback'，说明这是备用数据\n"
                "4. 保留关键数据（如温度、湿度等具体数值）\n"
                "5. 回答简洁明了"
            )

            # 格式化工具结果
            data_str = self._format_tool_results_for_llm(tool_results)

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"用户问题：{query}\n\n【真实数据】：\n{data_str}"}
            ]

            response = self._call_llm(messages, temperature=0.5)
            return response
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
        """基于规则生成响应（备用方案）"""
        if not tool_results:
            return f"抱歉，我无法处理您的查询: {query}"

        first_result = tool_results[0] if tool_results else {}

        if "error" in first_result:
            return f"工具执行失败: {first_result['error']}"

        tool_name = first_result.get("tool", "")
        source = first_result.get("source", "unknown")

        if tool_name == "weather":
            data = first_result.get("data", {})
            city = first_result.get("city", "")
            response = f"📍 {city}的天气情况（数据来源: {source}）：\n"
            response += f"  🌡️ 温度: {data.get('temp', 'N/A')}°C\n"
            response += f"  🌤️ 天气: {data.get('condition', 'N/A')}\n"
            response += f"  💧 湿度: {data.get('humidity', 'N/A')}%"
            if data.get('wind_speed'):
                response += f"\n  🌬️ 风速: {data.get('wind_speed')} km/h"
            return response

        elif tool_name == "news":
            news_list = first_result.get("news", [])
            response = f"📰 最新新闻（来源: {source}）：\n"
            for i, news in enumerate(news_list, 1):
                response += f"  {i}. {news.get('title', '无标题')}\n"
                if news.get('summary'):
                    response += f"     {news.get('summary')[:100]}\n"
            return response

        elif tool_name == "search":
            results = first_result.get("results", [])
            response = f"🔍 搜索结果（来源: {source}）：\n"
            for i, result in enumerate(results, 1):
                response += f"  {i}. {result.get('title', '无标题')}\n"
                if result.get('snippet'):
                    response += f"     {result.get('snippet')[:100]}\n"
            return response

        else:
            return f"已处理您的查询，结果: {json.dumps(first_result, ensure_ascii=False)}"

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
