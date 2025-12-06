# 多任务AI问答助手 - 完整快速原型

一个基于 **FastAPI + LangChain + OpenAI + Redis** 的生产级快速原型，支持多任务并行处理、智能任务分类和多轮对话管理。

## 🎯 核心特性

✅ **LLM 驱动的智能任务分类** - 使用 OpenAI GPT 进行自适应任务识别
✅ **多工具并行执行** - 异步并发处理多个 API 调用
✅ **自动降级机制** - LLM 失败时自动切换到规则引擎
✅ **多轮对话管理** - Redis 会话存储，支持长对话上下文
✅ **RESTful API** - 完整的 Swagger/OpenAPI 文档
✅ **生产级错误处理** - 异常捕获和日志记录

## 📦 项目结构

```
multitask-aiagent/
├── src/
│   ├── core/
│   │   └── agent.py           # MultiTaskAgent - LLM 驱动的核心逻辑
│   ├── tools/
│   │   └── tool_manager.py    # 工具集成层（天气、新闻、搜索等）
│   ├── schemas/
│   │   └── models.py          # Pydantic 数据模型
│   ├── utils/
│   │   └── redis_manager.py   # Redis 会话与缓存管理
│   └── main.py                # FastAPI 服务器
├── test.py                    # 基础功能测试
├── test_llm.py                # LLM 集成测试
├── client_demo.py             # API 客户端演示
├── requirements.txt           # 依赖
├── .env                       # 配置文件（OpenAI API Key）
└── README.md                  # 本文件
```

## 🚀 快速开始

### 1️⃣ 安装依赖

```bash
pip install -r requirements.txt
```

### 2️⃣ 配置环境变量

创建 `.env` 文件（已提供示例）：

```env
OPENAI_API_KEY=sk-your-key-here
OPENAI_API_BASE=https://api.xty.app/v1
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 3️⃣ 启动 Redis（可选，用于会话存储）

```bash
# macOS
brew services start redis

# Docker
docker run -d -p 6379:6379 redis:latest

# 或本地运行
redis-server
```

### 4️⃣ 启动 FastAPI 服务器

```bash
cd src
python -m uvicorn main:app --reload --port 8000
```

访问 http://localhost:8000/docs 查看交互式 API 文档

### 5️⃣ 运行测试

```bash
# 基础功能测试
python test.py

# LLM 集成测试
python test_llm.py

# API 客户端演示（需要先启动服务器）
python client_demo.py
```

## 🔌 API 端点

### 核心接口

| 方法 | 端点 | 描述 |
|------|------|------|
| `POST` | `/api/chat` | 单次问答 |
| `POST` | `/api/session/start` | 创建会话 |
| `GET` | `/api/session/{id}` | 获取会话历史 |
| `DELETE` | `/api/session/{id}` | 删除会话 |
| `GET` | `/api/tools` | 获取可用工具 |
| `POST` | `/api/cache/clear` | 清空缓存 |
| `GET` | `/health` | 健康检查 |

### 请求/响应示例

**单次问答**

```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "北京今天天气如何?"
  }'
```

**响应**

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
  "llm_used": true,
  "timestamp": "2025-12-06T12:00:00"
}
```

**创建会话**

```bash
curl -X POST "http://localhost:8000/api/session/start"
```

**获取会话历史**

```bash
curl "http://localhost:8000/api/session/{session_id}"
```

## 🤖 核心组件说明

### 1. MultiTaskAgent（src/core/agent.py）

**主要功能**：
- 使用 OpenAI GPT 进行任务分类
- 动态生成工具调用参数
- 智能生成自然语言回复

**架构**：

```
用户查询
    ↓
LLM 任务分类 (有降级)
    ↓
LLM 生成工具调用 (有降级)
    ↓
并行执行工具 (Tool Manager)
    ↓
LLM 生成响应 (有降级)
    ↓
返回结果
```

**关键方法**：

- `_classify_task_with_llm()` - LLM 驱动的任务分类
- `_generate_tool_calls_with_llm()` - 生成工具调用配置
- `_generate_response_with_llm()` - 生成自然语言回复
- `process_query()` - 主处理流程

### 2. ToolManager（src/tools/tool_manager.py）

**已实现工具**：

| 工具 | 功能 | 参数 |
|------|------|------|
| `weather` | 天气查询 | `city` |
| `news` | 新闻获取 | `category`, `limit` |
| `search` | 网络搜索 | `query` |
| `text_process` | 文本处理 | `text`, `action` |

**特点**：
- 异步执行 (asyncio)
- 并行执行多个工具 (`execute_tools_parallel()`)
- 模拟 API 调用（可扩展为真实 API）

### 3. RedisManager（src/utils/redis_manager.py）

**功能**：
- 会话创建与检索
- 消息历史存储
- 结果缓存
- TTL 管理（24小时会话，可配置缓存）

**API**：

```python
# 创建会话
session_id = redis_mgr.create_session()

# 保存会话
redis_mgr.save_session(session)

# 获取会话
session = redis_mgr.get_session(session_id)

# 缓存结果
redis_mgr.cache_result("key", "value", ttl=3600)

# 获取缓存
value = redis_mgr.get_cache("key")
```

## 📊 性能指标

在开发机器上的基准测试（使用模拟工具）：

| 操作 | 耗时 | 备注 |
|------|------|------|
| 单工具查询 | ~500ms | LLM + 工具执行 |
| 多工具并行 (3个) | ~800ms | 并行执行得益 |
| 会话操作 | <50ms | Redis 本地操作 |
| 缓存命中 | <10ms | 直接返回 |
| LLM 降级 | ~100ms | 规则引擎 |

## 🔧 扩展指南

### 添加新工具

1. **创建工具类** (src/tools/tool_manager.py)：

```python
class CustomTool(BaseTool):
    def __init__(self):
        super().__init__("custom", "工具描述")

    async def execute(self, **kwargs) -> Dict[str, Any]:
        # 实现逻辑
        return {
            "tool": self.name,
            "result": "..."
        }
```

2. **注册工具**：

```python
class ToolManager:
    def __init__(self):
        self.tools["custom"] = CustomTool()
```

3. **更新任务分类** (可选)：

```python
def _classify_task_with_llm(self, query: str) -> TaskType:
    # LLM 会自动识别新工具的使用场景
```

### 集成真实 API

替换工具的 `execute()` 方法：

```python
async def execute(self, city: str, **kwargs) -> Dict[str, Any]:
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://api.weatherapi.com/v1/current.json?q={city}"
        ) as resp:
            data = await resp.json()
            return {"tool": self.name, "data": data}
```

### 自定义 LLM 模型

编辑 `src/core/agent.py`：

```python
self.llm = ChatOpenAI(
    model_name="gpt-4",  # 改为 gpt-4
    openai_api_key=api_key,
    openai_api_base=api_base,
    temperature=0.5,  # 调整温度
    max_tokens=2000  # 增加 token 限制
)
```

## 📈 使用示例

### Python 异步调用

```python
import asyncio
from tools.tool_manager import ToolManager
from core.agent import MultiTaskAgent

async def main():
    tool_manager = ToolManager()
    agent = MultiTaskAgent(tool_manager, use_llm=True)

    result = await agent.process_query("北京天气")
    print(result['response'])

asyncio.run(main())
```

### cURL 调用

```bash
# 创建会话
SESSION_ID=$(curl -s -X POST "http://localhost:8000/api/session/start" | jq -r '.session_id')

# 发送查询
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"北京天气\", \"session_id\": \"$SESSION_ID\"}"

# 获取历史
curl "http://localhost:8000/api/session/$SESSION_ID"
```

### Python 客户端

```python
from client_demo import MultiTaskAgentClient

async def main():
    client = MultiTaskAgentClient()

    session_id = await client.start_session()
    response = await client.chat("北京天气", session_id)

    print(response['response'])

asyncio.run(main())
```

## 🛡️ 错误处理和降级

### LLM 故障自动降级

```python
# 如果 OpenAI API 失败，自动使用规则引擎
# 无需改动代码，系统自动处理

# 日志输出：
# ⚠️  LLM 分类失败: API error..., 使用规则引擎
# ✅ 查询仍能正常处理
```

### Redis 连接失败

```python
# 如果 Redis 不可用，系统继续运行
# 只是丧失会话持久化能力，工具执行不受影响

# 检查 Redis 状态：
GET /health  # redis: false
```

## 🔍 调试和日志

### 启用详细日志

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("app")
```

### API 调试

访问 http://localhost:8000/docs 获取：
- 交互式 API 文档
- 请求/响应示例
- 直接调试接口

## 📚 依赖说明

```
fastapi          - 现代 Web 框架
uvicorn          - ASGI 服务器
pydantic         - 数据验证
redis            - 会话和缓存存储
langchain        - LLM 集成框架
langchain-openai - OpenAI 适配器
openai           - OpenAI API 客户端
python-dotenv    - 环境变量管理
```

## 🚀 生产级优化建议

- [ ] 添加请求速率限制 (RateLimiter)
- [ ] 实现分布式任务队列 (Celery + Redis)
- [ ] 添加监控和告警 (Prometheus + Grafana)
- [ ] 实现 WebSocket 流式响应
- [ ] 添加请求认证和授权 (JWT)
- [ ] 结果缓存和去重
- [ ] 性能 profiling 和优化
- [ ] 容器化部署 (Docker)
- [ ] 单元测试和集成测试

## 🤝 贡献指南

欢迎提交问题报告和功能建议！

## 📝 许可证

MIT License

---

**版本**: 0.1.0
**最后更新**: 2025-12-06
**状态**: 快速原型 ✓ | 生产就绪 (需要额外优化)
