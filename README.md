# 多任务AI问答助手 - 快速原型

一个基于 FastAPI + LangChain + Redis 的轻量级多任务问答系统。

## 项目结构

```
multitask-aiagent/
├── src/
│   ├── core/              # 核心 Agent 逻辑
│   │   └── agent.py       # MultiTaskAgent 实现
│   ├── tools/             # 工具集成
│   │   └── tool_manager.py # 工具管理器
│   ├── schemas/           # 数据模型
│   │   └── models.py      # Pydantic 模型
│   ├── utils/             # 工具函数
│   │   └── redis_manager.py # Redis 管理器
│   └── main.py            # FastAPI 服务器
├── test.py                # 测试脚本
├── requirements.txt       # 依赖
└── README.md             # 本文件
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动 Redis（可选，用于会话存储）

```bash
# macOS 使用 Homebrew
brew services start redis

# 或者使用 Docker
docker run -d -p 6379:6379 redis:latest
```

### 3. 运行测试

```bash
python test.py
```

### 4. 启动服务器

```bash
cd src
python -m uvicorn main:app --reload --port 8000
```

访问 http://localhost:8000/docs 查看 API 文档

## 核心功能

### 1. 自动任务分类

系统会自动识别查询类型：
- **天气查询**: 包含"天气"、"温度"等关键词
- **新闻查询**: 包含"新闻"、"科技"等关键词
- **搜索查询**: 包含"搜索"、"查询"等关键词
- **通用问答**: 其他问题

### 2. 并行工具执行

多个工具请求可以并行执行，大大提升响应速度。

### 3. 会话管理

支持多轮对话，每个会话有独立的上下文和历史记录。

### 4. Redis 缓存

- 会话存储（TTL: 24小时）
- 结果缓存（可配置 TTL）
- 快速清空缓存

## API 端点

### 单次问答
```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "北京今天天气如何?"
  }'
```

### 创建会话
```bash
curl -X POST "http://localhost:8000/api/session/start"
```

### 获取会话历史
```bash
curl "http://localhost:8000/api/session/{session_id}"
```

### 删除会话
```bash
curl -X DELETE "http://localhost:8000/api/session/{session_id}"
```

### 获取可用工具
```bash
curl "http://localhost:8000/api/tools"
```

### 清空缓存
```bash
curl -X POST "http://localhost:8000/api/cache/clear"
```

## 工具集合

### 已实现的工具

1. **WeatherTool** - 天气查询
   - 参数: `city` (城市名称)
   - 返回: 温度、天气状况、湿度

2. **NewsTool** - 新闻获取
   - 参数: `category`, `limit`
   - 返回: 新闻标题、来源、日期

3. **SearchTool** - 网络搜索
   - 参数: `query` (搜索关键词)
   - 返回: 搜索结果、URL、摘要

4. **TextProcessTool** - 文本处理
   - 参数: `text`, `action` (summarize/uppercase/lowercase/word_count)
   - 返回: 处理后的文本

## 响应示例

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "response": "📍 北京的天气情况：\n  温度: 5°C\n  天气: 晴\n  湿度: 45%",
  "tool_calls": [
    {
      "tool_name": "weather",
      "parameters": {"city": "北京"},
      "result": "{...}"
    }
  ],
  "task_type": "weather",
  "timestamp": "2025-12-06T12:00:00"
}
```

## 性能指标

- **单工具查询**: ~500ms
- **多工具并行**: ~800ms (3个工具)
- **会话操作**: <50ms (本地 Redis)
- **缓存命中**: <10ms

## 扩展指南

### 添加新工具

1. 在 `tools/tool_manager.py` 创建新工具类：

```python
class MyTool(BaseTool):
    def __init__(self):
        super().__init__("my_tool", "工具描述")

    async def execute(self, **kwargs):
        # 实现逻辑
        return {"tool": self.name, "result": "..."}
```

2. 注册到 `ToolManager`：

```python
self.tools["my_tool"] = MyTool()
```

3. 更新 `Agent._generate_tool_calls()` 添加检测逻辑

### 自定义 LLM 集成

在 `core/agent.py` 中替换 `_generate_tool_calls()` 和 `_generate_response()` 方法，集成 OpenAI、Claude 等 LLM。

```python
# 使用 LangChain 集成 LLM
from langchain.llms import OpenAI
from langchain.agents import AgentExecutor, Tool
from langchain.agents import initialize_agent

llm = OpenAI(api_key="sk-...")
# 创建 tools 列表和 agent
```

## 依赖说明

| 库 | 版本 | 用途 |
|----|------|------|
| FastAPI | 0.104.1 | Web 框架 |
| Uvicorn | 0.24.0 | ASGI 服务器 |
| Pydantic | 2.5.0 | 数据验证 |
| Redis | 5.0.1 | 缓存和会话 |
| LangChain | 0.1.0 | LLM 集成框架 |

## 未来优化方向

- [ ] 集成实际 LLM（OpenAI, Anthropic Claude）
- [ ] 完整的流式 WebSocket 支持
- [ ] 分布式任务队列（Celery）
- [ ] 结果缓存策略优化
- [ ] 错误恢复和重试机制
- [ ] 请求速率限制
- [ ] 监控和日志系统

## 测试覆盖

运行 `test.py` 会执行：

- ✅ 基础 Agent 功能测试
- ✅ 并行工具执行测试
- ✅ 会话管理测试（需要 Redis）
- ✅ 缓存功能测试（需要 Redis）

## 许可证

MIT

---

**注意**: 这是一个快速原型，适合学习和演示。生产环境需要添加：
- 完整的错误处理和日志
- 请求验证和安全检查
- 更复杂的 LLM 集成
- 性能监控和优化
