"""
工具集成层 - 集成外部API和本地工具
"""
import asyncio
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from datetime import datetime
import httpx


class BaseTool(ABC):
    """工具基类"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """执行工具"""
        pass


class WeatherTool(BaseTool):
    """天气查询工具（使用 wttr.in API）"""

    def __init__(self):
        super().__init__(
            "weather",
            "查询指定城市的天气情况"
        )
        # wttr.in 免费天气 API
        self.base_url = "https://wttr.in"

    async def execute(self, city: str = "北京", **kwargs) -> Dict[str, Any]:
        """调用真实天气 API"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # wttr.in API，format=j1 返回 JSON 格式
                url = f"{self.base_url}/{city}?format=j1&lang=zh"
                response = await client.get(url)

                if response.status_code == 200:
                    data = response.json()
                    current = data.get("current_condition", [{}])[0]

                    return {
                        "tool": self.name,
                        "source": "wttr.in",
                        "city": city,
                        "data": {
                            "temp": current.get("temp_C", "未知"),
                            "feels_like": current.get("FeelsLikeC", "未知"),
                            "condition": current.get("lang_zh", [{}])[0].get("value", current.get("weatherDesc", [{}])[0].get("value", "未知")),
                            "humidity": current.get("humidity", "未知"),
                            "wind_speed": current.get("windspeedKmph", "未知"),
                            "wind_dir": current.get("winddir16Point", "未知"),
                            "visibility": current.get("visibility", "未知"),
                            "uv_index": current.get("uvIndex", "未知"),
                        },
                        "timestamp": datetime.now().isoformat(),
                        "source": "wttr.in"
                    }
                else:
                    return await self._fallback_weather(city)
        except Exception as e:
            print(f"⚠️ 天气 API 调用失败: {e}，使用备用数据")
            return await self._fallback_weather(city)

    async def _fallback_weather(self, city: str) -> Dict[str, Any]:
        """备用天气数据"""
        fallback_data = {
            "北京": {"temp": 5, "condition": "晴", "humidity": 45},
            "上海": {"temp": 8, "condition": "多云", "humidity": 65},
            "广州": {"temp": 15, "condition": "晴", "humidity": 55},
            "深圳": {"temp": 16, "condition": "晴", "humidity": 60},
        }
        result = fallback_data.get(city, {"temp": "未知", "condition": "未知", "humidity": "未知"})
        return {
            "tool": self.name,
            "city": city,
            "data": result,
            "timestamp": datetime.now().isoformat(),
            "source": "fallback"
        }


class NewsTool(BaseTool):
    """新闻获取工具（使用真实 RSS 源）"""

    def __init__(self):
        super().__init__(
            "news",
            "获取最新新闻"
        )
        # 新闻 RSS 源
        self.rss_sources = {
            "tech": "https://feeds.bbci.co.uk/news/technology/rss.xml",
            "general": "https://feeds.bbci.co.uk/news/rss.xml",
            "science": "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
        }

    async def execute(self, category: str = "tech", limit: int = 5, **kwargs) -> Dict[str, Any]:
        """获取真实新闻"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                rss_url = self.rss_sources.get(category, self.rss_sources["tech"])
                response = await client.get(rss_url)

                if response.status_code == 200:
                    # 简单解析 RSS XML
                    news_items = self._parse_rss(response.text, limit)
                    return {
                        "tool": self.name,
                        "category": category,
                        "news": news_items,
                        "timestamp": datetime.now().isoformat(),
                        "source": "BBC RSS"
                    }
                else:
                    return await self._fallback_news(category, limit)
        except Exception as e:
            print(f"⚠️ 新闻 API 调用失败: {e}，使用备用数据")
            return await self._fallback_news(category, limit)

    def _parse_rss(self, xml_content: str, limit: int) -> List[Dict[str, str]]:
        """简单解析 RSS XML"""
        import re
        news_items = []

        # 使用正则表达式提取 item
        items = re.findall(r'<item>(.*?)</item>', xml_content, re.DOTALL)

        for item in items[:limit]:
            title_match = re.search(r'<title><!\[CDATA\[(.*?)\]\]></title>|<title>(.*?)</title>', item)
            link_match = re.search(r'<link>(.*?)</link>', item)
            pub_date_match = re.search(r'<pubDate>(.*?)</pubDate>', item)
            desc_match = re.search(r'<description><!\[CDATA\[(.*?)\]\]></description>|<description>(.*?)</description>', item, re.DOTALL)

            title = ""
            if title_match:
                title = title_match.group(1) or title_match.group(2) or ""

            description = ""
            if desc_match:
                description = desc_match.group(1) or desc_match.group(2) or ""
                # 清理 HTML 标签
                description = re.sub(r'<[^>]+>', '', description).strip()[:200]

            news_items.append({
                "title": title.strip(),
                "link": link_match.group(1) if link_match else "",
                "date": pub_date_match.group(1) if pub_date_match else "",
                "summary": description
            })

        return news_items

    async def _fallback_news(self, category: str, limit: int) -> Dict[str, Any]:
        """备用新闻数据"""
        news_samples = [
            {"title": "AI大模型最新突破：多模态能力提升", "source": "TechNews", "date": "2025-12-07", "summary": "人工智能领域取得重大进展"},
            {"title": "量子计算应用前景广阔", "source": "ScienceDaily", "date": "2025-12-06", "summary": "量子计算技术日趋成熟"},
            {"title": "新能源汽车销量创新高", "source": "AutoNews", "date": "2025-12-05", "summary": "电动汽车市场持续增长"},
        ]
        return {
            "tool": self.name,
            "category": category,
            "news": news_samples[:limit],
            "timestamp": datetime.now().isoformat(),
            "source": "fallback"
        }


class SearchTool(BaseTool):
    """搜索工具（使用 DuckDuckGo）"""

    def __init__(self):
        super().__init__(
            "search",
            "搜索相关信息"
        )

    async def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """使用 DuckDuckGo Instant Answer API"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # DuckDuckGo Instant Answer API
                url = "https://api.duckduckgo.com/"
                params = {
                    "q": query,
                    "format": "json",
                    "no_html": 1,
                    "skip_disambig": 1
                }
                response = await client.get(url, params=params)

                if response.status_code == 200:
                    data = response.json()
                    results = []

                    # 主要结果
                    if data.get("Abstract"):
                        results.append({
                            "title": data.get("Heading", query),
                            "url": data.get("AbstractURL", ""),
                            "snippet": data.get("Abstract", "")
                        })

                    # 相关话题
                    for topic in data.get("RelatedTopics", [])[:3]:
                        if isinstance(topic, dict) and topic.get("Text"):
                            results.append({
                                "title": topic.get("Text", "")[:50],
                                "url": topic.get("FirstURL", ""),
                                "snippet": topic.get("Text", "")
                            })

                    if not results:
                        results = await self._fallback_search(query)

                    return {
                        "tool": self.name,
                        "query": query,
                        "results": results[:5],
                        "timestamp": datetime.now().isoformat(),
                        "source": "DuckDuckGo"
                    }
                else:
                    return await self._fallback_search_result(query)
        except Exception as e:
            print(f"⚠️ 搜索 API 调用失败: {e}")
            return await self._fallback_search_result(query)

    async def _fallback_search(self, query: str) -> List[Dict[str, str]]:
        """备用搜索结果"""
        return [
            {"title": f"关于'{query}'的搜索结果", "url": f"https://www.google.com/search?q={query}", "snippet": f"这是关于{query}的相关信息..."}
        ]

    async def _fallback_search_result(self, query: str) -> Dict[str, Any]:
        """备用搜索返回"""
        return {
            "tool": self.name,
            "query": query,
            "results": await self._fallback_search(query),
            "timestamp": datetime.now().isoformat(),
            "source": "fallback"
        }


class TextProcessTool(BaseTool):
    """文本处理工具（本地）"""

    def __init__(self):
        super().__init__(
            "text_process",
            "处理和转换文本格式"
        )

    async def execute(self, text: str, action: str = "summarize", **kwargs) -> Dict[str, Any]:
        """文本处理"""
        result = ""

        if action == "summarize":
            result = text[:100] + "..." if len(text) > 100 else text
        elif action == "uppercase":
            result = text.upper()
        elif action == "lowercase":
            result = text.lower()
        elif action == "word_count":
            result = f"字数: {len(text)}, 词数: {len(text.split())}"

        return {
            "tool": self.name,
            "action": action,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }


class ToolManager:
    """工具管理器"""

    def __init__(self):
        self.tools = {
            "weather": WeatherTool(),
            "news": NewsTool(),
            "search": SearchTool(),
            "text_process": TextProcessTool(),
        }

    async def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """执行单个工具"""
        if tool_name not in self.tools:
            return {
                "error": f"工具 '{tool_name}' 不存在",
                "available_tools": list(self.tools.keys())
            }

        try:
            return await self.tools[tool_name].execute(**kwargs)
        except Exception as e:
            return {"error": str(e), "tool": tool_name}

    async def execute_tools_parallel(self, tool_requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """并行执行多个工具"""
        tasks = [
            self.execute_tool(req["tool"], **req.get("params", {}))
            for req in tool_requests
        ]
        return await asyncio.gather(*tasks)

    def get_tool_descriptions(self) -> Dict[str, str]:
        """获取所有工具描述"""
        return {
            name: tool.description
            for name, tool in self.tools.items()
        }
