# 🚀 快速开始指南

## ✅ 项目状态

```
✓ 依赖安装完成
✓ 所有模块可导入
✓ 工具加载正常
✓ FastAPI 应用就绪
⚠ Redis 可选（用于会话持久化）
⚠ OpenAI API Key 可选（支持规则引擎降级）
```

## 🏃 3 步启动

### 1️⃣ 启动 FastAPI 服务器

```bash
cd /Volumes/learning/multitask-aiagent
cd src
python -m uvicorn main:app --reload --port 8000
```

输出应该类似于：
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxx] using StatReload
INFO:     Started server process [xxx]
INFO:     Application startup complete
```

### 2️⃣ 访问 API 文档

打开浏览器访问: **http://localhost:8000/docs**

你会看到 Swagger UI，可以直接在浏览器中测试 API。

### 3️⃣ 测试接口

#### 方式 A：使用 curl

```bash
# 创建会话
curl -X POST "http://localhost:8000/api/session/start"

# 发送查询
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"query":"北京今天天气如何?"}'

# 获取可用工具
curl "http://localhost:8000/api/tools"

# 健康检查
curl "http://localhost:8000/health"
```

#### 方式 B：使用 Python

```python
import asyncio
import sys
import os

sys.path.insert(0, 'src')

from tools.tool_manager import ToolManager
from core.agent import MultiTaskAgent

async def main():
    tool_manager = ToolManager()
    agent = MultiTaskAgent(tool_manager, use_llm=False)

    result = await agent.process_query("北京天气")
    print(result['response'])

asyncio.run(main())
```

#### 方式 C：使用 JavaScript/Fetch

```javascript
async function query(text) {
  const response = await fetch('http://localhost:8000/api/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ query: text })
  });
  const data = await response.json();
  console.log(data.response);
}

query('北京天气');
```

## 🔧 可选配置

### 启用 Redis（用于会话持久化）

```bash
# macOS
brew services start redis

# Docker
docker run -d -p 6379:6379 redis:latest

# Linux
sudo systemctl start redis-server
```

验证 Redis 运行：
```bash
redis-cli ping
# 输出: PONG
```

### 配置 OpenAI API

编辑 `.env` 文件，添加你的 API Key：

```env
OPENAI_API_KEY=sk-your-actual-key-here
OPENAI_API_BASE=https://api.openai.com/v1
```

或使用代理：
```env
OPENAI_API_KEY=sk-your-key
OPENAI_API_BASE=https://api.xty.app/v1
```

## 📝 测试脚本

### 运行基础功能测试

```bash
python test.py
```

### 运行 LLM 集成测试

```bash
python test_llm.py
```

### 运行 API 客户端演示

```bash
# 首先启动服务器（另一个终端）
python client_demo.py
```

## 🎯 API 端点一览

| 方法 | 端点 | 功能 |
|------|------|------|
| `POST` | `/api/chat` | 单次问答 |
| `POST` | `/api/session/start` | 创建会话 |
| `GET` | `/api/session/{id}` | 获取会话历史 |
| `DELETE` | `/api/session/{id}` | 删除会话 |
| `GET` | `/api/tools` | 获取可用工具 |
| `POST` | `/api/cache/clear` | 清空缓存 |
| `GET` | `/health` | 健康检查 |
| `GET` | `/` | API 信息 |

## 💡 使用示例

### 示例 1：天气查询

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query":"北京今天天气怎么样?"}'
```

响应：
```json
{
  "session_id": "...",
  "response": "📍 北京的天气情况：\n  温度: 5°C\n  天气: 晴\n  湿度: 45%",
  "task_type": "weather",
  "tool_calls": [...]
}
```

### 示例 2：多轮对话

```bash
# 1. 创建会话
SESSION=$(curl -s -X POST http://localhost:8000/api/session/start | jq -r '.session_id')

# 2. 第一个问题
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"北京天气\", \"session_id\":\"$SESSION\"}"

# 3. 第二个问题（会话保留）
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"上海天气\", \"session_id\":\"$SESSION\"}"

# 4. 查看对话历史
curl http://localhost:8000/api/session/$SESSION
```

## 🐛 常见问题

### Q1: 启动时报错 "Address already in use"

**A:** 端口 8000 被占用。改用其他端口：

```bash
python -m uvicorn main:app --reload --port 8001
```

### Q2: Redis 连接失败

**A:** Redis 是可选的。系统会自动降级使用内存存储。如需会话持久化，启动 Redis。

### Q3: OpenAI API 调用失败

**A:** 系统会自动降级使用规则引擎。如要使用 LLM，配置 `.env` 文件。

### Q4: 如何关闭服务器？

**A:** 按 `Ctrl+C`（Windows/Mac/Linux 通用）

### Q5: 如何修改监听地址？

**A:** 修改启动命令：

```bash
# 只监听本地
python -m uvicorn main:app --reload --host 127.0.0.1

# 监听所有接口（生产不推荐）
python -m uvicorn main:app --reload --host 0.0.0.0
```

## 📚 项目文档

- **INDEX.md** - 项目完整索引（推荐先读）
- **QUICKSTART.md** - 详细的快速开始和 API 文档
- **PROJECT_SUMMARY.md** - 系统架构和性能指标
- **INSTALL_GUIDE.md** - 依赖安装指南

## 🔗 相关资源

- FastAPI 官方文档: https://fastapi.tiangolo.com/
- OpenAI API 文档: https://platform.openai.com/docs/
- Redis 文档: https://redis.io/docs/
- Python asyncio: https://docs.python.org/3/library/asyncio.html

## ✅ 下一步

1. ✓ 阅读 `INDEX.md` 了解项目结构
2. ✓ 运行本地测试脚本验证功能
3. ✓ 启动 FastAPI 服务器
4. ✓ 在 Swagger UI 中测试 API
5. ✓ 修改代码添加自己的工具

---

**项目完成！祝你使用愉快！** 🎉

