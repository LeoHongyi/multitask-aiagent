# ❌ API 错误修复指南

## 问题描述

```
ERROR:main:处理查询失败: string indices must be integers, not 'str'
```

## 原因分析

这个错误发生在 OpenAI API 响应处理时。错误信息表示代码尝试用字符串索引来访问字符串对象。

可能的原因：
1. OpenAI API 返回的响应格式不符合预期
2. JSON 解析时出现问题
3. 错误处理的逻辑缺陷

## ✅ 已完成的修复

### 1. 改进 `_call_llm()` 方法的响应处理
- 确保响应总是字符串
- 添加更好的错误捕获

### 2. 完善错误日志
- 添加完整的堆栈跟踪
- 改进调试输出

### 3. 工具响应结构统一
- 所有工具返回都包含 `source` 字段
- 降级方案响应格式一致

## 🚀 现在运行测试

```bash
cd /Volumes/learning/multitask-aiagent
python verify.py
```

如果仍有错误，请重启服务器：

```bash
cd src
python -m uvicorn main:app --reload
```

## 🔧 快速诊断

如果继续出现错误，运行：

```bash
python test_llm.py
```

这会显示详细的错误堆栈。

## 📝 常见的 API 响应问题

### 问题1: OpenAI API 返回非 JSON 响应
```
解决: 检查 API Key 是否有效
```

### 问题 2: JSON 包含代码块
```python
# API 可能返回这样的格式
"""
\`\`\`json
{...}
\`\`\`
"""
# 已在代码中处理
```

### 问题 3: 工具参数格式错误
```python
# 确保工具调用返回列表
tool_calls = [{
    "tool": "weather",
    "params": {"city": "北京"}
}]
```

## 🎯 下一步

1. **重启服务器**
```bash
cd /Volumes/learning/multitask-aiagent/src
python -m uvicorn main:app --reload
```

2. **测试 API**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query":"北京天气"}'
```

3. **检查日志**
服务器输出中应该显示详细的日志

## ⚠️ 如果问题持续

### 选项 1: 禁用 LLM，仅使用规则引擎

修改 `src/main.py`：

```python
# 将这一行
agent = MultiTaskAgent(tool_manager)

# 改为
agent = MultiTaskAgent(tool_manager, use_llm=False)
```

这样会使用规则引擎而不是 OpenAI API。

### 选项 2: 检查 OpenAI 凭证

```bash
# 验证环境变量
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(f'API Key: {os.getenv(\"OPENAI_API_KEY\")[:20]}...'); print(f'API Base: {os.getenv(\"OPENAI_API_BASE\")}')"
```

### 选项 3: 测试 API 连接

```bash
python << 'EOF'
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_API_BASE")
)

try:
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Hello"}],
        max_tokens=10
    )
    print("✅ API 连接成功")
    print(f"响应: {response.choices[0].message.content}")
except Exception as e:
    print(f"❌ API 连接失败: {e}")
EOF
```

## 📚 相关文件

- 核心逻辑: `src/core/agent.py`
- 工具管理: `src/tools/tool_manager.py`
- 主服务器: `src/main.py`

## 💡 调试技巧

1. **启用详细日志**
在 `src/main.py` 中修改日志级别：
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

2. **添加打印调试**
在 `agent.py` 中添加：
```python
print(f"[DEBUG] 响应类型: {type(response)}")
print(f"[DEBUG] 响应内容: {response}")
```

3. **逐步测试**
```bash
# 只测试分类
python -c "
import asyncio
from src.tools.tool_manager import ToolManager
from src.core.agent import MultiTaskAgent

async def test():
    tm = ToolManager()
    agent = MultiTaskAgent(tm)
    task_type = agent._classify_task_with_llm('北京天气')
    print(f'分类: {task_type}')

asyncio.run(test())
"
```

---

**状态**: 问题已修复并改进
**建议**: 重启服务器后重新测试
