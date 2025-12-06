# 🏢 智能客服中心使用指南

## 🎯 系统概述

智能客服中心是一个基于AI的专业客户服务系统，支持订单查询、物流追踪、退换货处理、技术支持等多种客服场景。

### 核心特性
- 🤖 **智能分类**: 自动识别客户问题类型
- 🔍 **多工具集成**: 订单、物流、退款、知识库等工具
- 📝 **工单管理**: 完整的工单生命周期管理
- 👥 **客户管理**: 客户信息和历史记录
- 💬 **多渠道接入**: 支持Web、APP、微信等多种渠道
- 📊 **数据统计**: 客服绩效和服务质量分析

---

## 🚀 快速开始

### 1. 启动服务

```bash
cd /Volumes/learning/multitask-aiagent/src
python -m uvicorn main:app --reload
```

服务启动后，访问：http://localhost:8000

### 2. API文档

- **客服聊天接口**: http://localhost:8000/docs
- **客服管理接口**: http://localhost:8000/customer-service/docs
- **健康检查**: http://localhost:8000/customer-service/health

---

## 🛠️ 主要功能模块

### 1. 智能客服对话

**接口**: `POST /api/customer-service/chat`

**功能**: 智能识别客户问题并自动回复

**示例请求**:
```bash
curl -X POST "http://localhost:8000/api/customer-service/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "我的订单ORD001到哪里了？",
    "session_id": "session_123",
    "channel": "web"
  }'
```

**示例响应**:
```json
{
  "response": "您的订单ORD001当前状态是：已送达。物流状态：已送达，最新更新：2025-12-04 16:20 已签收。希望这些信息对您有帮助！",
  "task_type": "logistics_tracking",
  "tool_calls": [
    {
      "tool": "logistics_tracking",
      "params": {"tracking_number": "SF1234567890"}
    }
  ],
  "tool_results": [...],
  "session_id": "session_123",
  "channel": "web",
  "timestamp": "2025-12-07T10:30:00",
  "agent_type": "customer_service",
  "llm_used": true
}
```

### 2. 工单管理系统

#### 创建工单

**接口**: `POST /customer-service/tickets`

**示例请求**:
```bash
curl -X POST "http://localhost:8000/customer-service/tickets" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "C001",
    "title": "订单物流问题",
    "description": "订单ORD001已经超过预计送达时间还没收到",
    "category": "logistics_issue",
    "priority": "medium",
    "channel": "web",
    "related_order_id": "ORD001"
  }'
```

#### 查询工单

**接口**: `GET /customer-service/tickets/{ticket_id}`

#### 更新工单

**接口**: `PUT /customer-service/tickets/{ticket_id}`

### 3. 客户信息查询

**接口**: `POST /customer-service/customers/lookup`

**示例请求**:
```bash
curl -X POST "http://localhost:8000/customer-service/customers/lookup" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "13800138000",
    "search_type": "phone"
  }'
```

### 4. 知识库搜索

**接口**: `GET /customer-service/knowledge/search`

**示例请求**:
```bash
curl -X GET "http://localhost:8000/customer-service/knowledge/search?query=退换货&limit=3"
```

---

## 🎯 支持的问题类型

### 1. 订单相关问题
- **订单查询**: "我的订单ORD001到哪了？"
- **订单修改**: "我想修改订单的收货地址"
- **订单取消**: "我要取消订单ORD002"

### 2. 物流问题
- **物流查询**: "快递单号SF1234567890的物流信息"
- **配送问题**: "为什么我的快递还没到？"

### 3. 退换货问题
- **退款申请**: "我要退款，订单号ORD001"
- **换货流程**: "收到的商品有问题，想换一个"

### 4. 技术支持
- **产品问题**: "手机无法开机怎么办？"
- **使用指导**: "这个功能怎么使用？"

### 5. 投诉建议
- **服务投诉**: "客服态度很差"
- **产品投诉**: "产品质量有问题"

---

## 📊 测试用例集

### 基础功能测试

#### 1. 订单查询测试
```bash
# 测试1: 订单号查询
curl -X POST "http://localhost:8000/api/customer-service/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "查询订单ORD001的状态"}'

# 测试2: 模糊订单查询
curl -X POST "http://localhost:8000/api/customer-service/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "我的订单什么时候能到？"}'
```

#### 2. 物流追踪测试
```bash
# 测试1: 快递单号查询
curl -X POST "http://localhost:8000/api/customer-service/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "快递单号SF1234567890到哪了？"}'

# 测试2: 物流状态查询
curl -X POST "http://localhost:8000/api/customer-service/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "我的包裹为什么还没送到？"}'
```

#### 3. 退款处理测试
```bash
# 测试1: 退款申请
curl -X POST "http://localhost:8000/api/customer-service/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "我要申请退款，订单ORD001有质量问题"}'

# 测试2: 退款进度查询
curl -X POST "http://localhost:8000/api/customer-service/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "退款申请REF202512070001处理得怎么样了？"}'
```

#### 4. 客户识别测试
```bash
# 测试1: 手机号识别
curl -X POST "http://localhost:8000/api/customer-service/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "我叫张三，手机号是13800138000，查询我的订单"}'

# 测试2: 邮箱识别
curl -X POST "http://localhost:8000/api/customer-service/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "我的邮箱是zhangsan@example.com，有一个退货问题"}'
```

### 复杂场景测试

#### 1. 多问题组合测试
```bash
curl -X POST "http://localhost:8000/api/customer-service/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "我是李四（13900139000），订单ORD003的商品有问题，既想退货又要投诉，你们的服务太差了！"}'
```

#### 2. 紧急问题测试
```bash
curl -X POST "http://localhost:8000/api/customer-service/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "订单ORD001价值5999元的商品运输损坏，要求立即处理并赔偿！"}'
```

#### 3. 升级处理测试
```bash
curl -X POST "http://localhost:8000/api/customer-service/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "我要找你们经理，这个问题太严重了，我要去媒体曝光！"}'
```

---

## 🛠️ 管理功能测试

### 1. 工单管理测试
```bash
# 创建工单
curl -X POST "http://localhost:8000/customer-service/tickets" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "C001",
    "title": "测试工单",
    "description": "这是一个测试工单",
    "category": "order_issue",
    "priority": "medium"
  }'

# 查询工单（使用返回的ticket_id）
curl -X GET "http://localhost:8000/customer-service/tickets/TKxxxxxxxx"

# 更新工单
curl -X PUT "http://localhost:8000/customer-service/tickets/TKxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "resolved",
    "resolution": "问题已解决"
  }'
```

### 2. 客户管理测试
```bash
# 查询客户
curl -X POST "http://localhost:8000/customer-service/customers/lookup" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "13800138000",
    "search_type": "phone"
  }'

# 查询客户工单历史
curl -X GET "http://localhost:8000/customer-service/customers/C001/tickets"
```

### 3. 统计信息测试
```bash
# 客服绩效统计
curl -X GET "http://localhost:8000/customer-service/agents/stats"

# 特定客服统计
curl -X GET "http://localhost:8000/customer-service/agents/stats?agent_id=agent001"
```

---

## 🔧 开发调试

### 1. 日志查看
服务启动后，可以在控制台看到详细的处理日志：
```
INFO:customer_service_agent:客服对话请求: 查询订单ORD001的状态...
INFO:tools.customer_service_tools:执行工具: order_query
INFO:customer_service_agent:任务分类: order_query
```

### 2. 错误排查
常见错误及解决方案：

#### OpenAI API 错误
```
❌ LLM API 调用错误: ...
```
**解决**: 检查 `.env` 文件中的 `OPENAI_API_KEY` 和 `OPENAI_API_BASE`

#### Redis 连接错误
```
⚠️ Redis连接失败: ...
```
**解决**: 确保Redis服务已启动，或修改配置使用内存存储

#### 工具执行错误
```
⚠️ 工具执行失败: ...
```
**解决**: 检查工具参数是否正确，查看详细错误信息

### 3. 配置调整

#### 环境变量配置
在 `.env` 文件中：
```env
OPENAI_API_KEY=your_api_key
OPENAI_API_BASE=https://api.xty.app/v1
REDIS_URL=redis://localhost:6379
```

#### Agent 配置
在 `main.py` 中：
```python
# 禁用LLM，使用规则引擎
cs_agent = CustomerServiceAgent(use_llm=False)

# 启用LLM（默认）
cs_agent = CustomerServiceAgent(use_llm=True)
```

---

## 📈 性能优化

### 1. 响应时间优化
- 使用Redis缓存客户信息和工单数据
- 并行执行多个工具调用
- 优化LLM prompt长度

### 2. 可扩展性优化
- 添加更多客服工具
- 支持更多接入渠道
- 增加更多的业务规则

### 3. 稳定性优化
- 完善错误处理机制
- 添加重试和降级策略
- 实现服务健康监控

---

## 🎯 最佳实践

### 1. 对话设计
- 保持回复简洁明了
- 表达理解和共情
- 提供具体的解决方案
- 主动询问是否需要其他帮助

### 2. 工具使用
- 合理配置工具参数
- 处理工具执行失败的情况
- 提供有意义的错误信息

### 3. 数据管理
- 定期清理过期数据
- 保护客户隐私信息
- 建立数据备份机制

---

## 🔮 未来扩展

### 1. 智能化增强
- 添加情感分析
- 实现个性化回复
- 支持语音交互

### 2. 功能扩展
- 添加更多业务工具
- 支持多语言
- 集成第三方客服系统

### 3. 数据分析
- 客户行为分析
- 服务质量评估
- 业务趋势预测

---

**✅ 智能客服中心已完成改造！**

**🚀 现在您可以：**
1. 使用 `/api/customer-service/chat` 进行智能客服对话
2. 使用 `/customer-service/*` 进行客服管理操作
3. 查看完整的API文档和测试示例

**📞 如有问题，请查看日志或联系技术支持！**