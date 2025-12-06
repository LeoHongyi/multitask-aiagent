import { useState, useEffect } from 'react'
import './CustomerService.css'

// Agent API 调用
const API_BASE = ''

async function sendAgentMessage(message, customerId = 'C001', orderId = null) {
  const response = await fetch(`${API_BASE}/api/agent/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, customer_id: customerId, order_id: orderId })
  })
  return response.json()
}

async function getAgentStats() {
  const response = await fetch(`${API_BASE}/api/agent/stats`)
  return response.json()
}

async function getOrders() {
  const response = await fetch(`${API_BASE}/api/agent/orders`)
  return response.json()
}

async function getWorkflowDetail(workflowId) {
  const response = await fetch(`${API_BASE}/api/agent/workflow/${workflowId}`)
  return response.json()
}

function CustomerService() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [stats, setStats] = useState(null)
  const [orders, setOrders] = useState([])
  const [selectedOrder, setSelectedOrder] = useState(null)
  const [workflowDetails, setWorkflowDetails] = useState(null)
  const [activeTab, setActiveTab] = useState('chat')

  useEffect(() => {
    loadInitialData()
  }, [])

  const loadInitialData = async () => {
    try {
      const [statsData, ordersData] = await Promise.all([
        getAgentStats(),
        getOrders()
      ])
      setStats(statsData)
      setOrders(ordersData.orders || [])
    } catch (error) {
      console.error('Failed to load data:', error)
    }
  }

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: input,
      timestamp: new Date().toLocaleTimeString()
    }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const response = await sendAgentMessage(input, 'C001', selectedOrder)

      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: response.response,
        timestamp: new Date().toLocaleTimeString(),
        workflowId: response.workflow_id,
        taskType: response.task_type,
        agentChain: response.agent_chain,
        stepsCompleted: response.steps_completed
      }
      setMessages(prev => [...prev, assistantMessage])

      // 刷新统计
      const newStats = await getAgentStats()
      setStats(newStats)
    } catch (error) {
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: 'assistant',
        content: '抱歉，服务暂时不可用，请稍后重试。',
        timestamp: new Date().toLocaleTimeString()
      }])
    } finally {
      setIsLoading(false)
    }
  }

  const handleQuickAction = (action) => {
    const quickMessages = {
      'order_query': '帮我查询订单 ORD001 的物流信息',
      'refund': '我想申请订单 ORD002 退款',
      'complaint': '我要投诉，订单太慢了一直不发货',
      'exchange': '订单 ORD002 的商品有问题，我要换货'
    }
    setInput(quickMessages[action] || '')
  }

  const viewWorkflow = async (workflowId) => {
    try {
      const detail = await getWorkflowDetail(workflowId)
      setWorkflowDetails(detail)
    } catch (error) {
      console.error('Failed to load workflow:', error)
    }
  }

  const clearChat = () => {
    setMessages([])
    setWorkflowDetails(null)
  }

  return (
    <div className="customer-service-page">
      {/* 左侧面板 */}
      <aside className="cs-sidebar">
        <div className="cs-logo">
          <span className="logo-icon">🤖</span>
          <span>多Agent客服系统</span>
        </div>

        <div className="cs-tabs">
          <button
            className={activeTab === 'chat' ? 'active' : ''}
            onClick={() => setActiveTab('chat')}
          >
            💬 智能客服
          </button>
          <button
            className={activeTab === 'orders' ? 'active' : ''}
            onClick={() => setActiveTab('orders')}
          >
            📦 订单管理
          </button>
          <button
            className={activeTab === 'stats' ? 'active' : ''}
            onClick={() => setActiveTab('stats')}
          >
            📊 系统统计
          </button>
        </div>

        {/* Agent 列表 */}
        <div className="agent-list">
          <h3>Agent 团队</h3>
          {stats?.agents?.map(agent => (
            <div key={agent.role} className="agent-item">
              <span className="agent-icon">
                {agent.role === 'router' && '🔀'}
                {agent.role === 'order' && '📦'}
                {agent.role === 'refund' && '💰'}
                {agent.role === 'complaint' && '📢'}
                {agent.role === 'supervisor' && '👔'}
              </span>
              <div className="agent-info">
                <span className="agent-name">{agent.name}</span>
                <span className="agent-desc">{agent.description}</span>
              </div>
            </div>
          ))}
        </div>
      </aside>

      {/* 主内容区 */}
      <main className="cs-main">
        {activeTab === 'chat' && (
          <>
            <header className="cs-header">
              <h1>🎧 智能客服中心</h1>
              <p>多Agent协同处理 · 自动任务分发 · 智能升级</p>
            </header>

            {/* 快捷操作 */}
            <div className="quick-actions">
              <button onClick={() => handleQuickAction('order_query')}>
                📦 查询订单
              </button>
              <button onClick={() => handleQuickAction('refund')}>
                💰 申请退款
              </button>
              <button onClick={() => handleQuickAction('exchange')}>
                🔄 申请换货
              </button>
              <button onClick={() => handleQuickAction('complaint')}>
                📢 投诉建议
              </button>
              <button onClick={clearChat} className="clear-btn">
                🗑️ 清空对话
              </button>
            </div>

            {/* 选择订单 */}
            <div className="order-selector">
              <label>关联订单：</label>
              <select
                value={selectedOrder || ''}
                onChange={(e) => setSelectedOrder(e.target.value || null)}
              >
                <option value="">不关联订单</option>
                {orders.map(order => (
                  <option key={order.order_id} value={order.order_id}>
                    {order.order_id} - {order.product_name}
                  </option>
                ))}
              </select>
            </div>

            {/* 聊天区域 */}
            <div className="chat-area">
              {messages.length === 0 && (
                <div className="empty-chat">
                  <div className="empty-icon">💬</div>
                  <h2>欢迎使用多Agent智能客服</h2>
                  <p>我们的Agent团队将协同为您服务</p>
                  <div className="workflow-intro">
                    <div className="flow-step">🔀 路由Agent 分析意图</div>
                    <div className="flow-arrow">→</div>
                    <div className="flow-step">📦 专业Agent 处理任务</div>
                    <div className="flow-arrow">→</div>
                    <div className="flow-step">👔 主管Agent 审核升级</div>
                  </div>
                </div>
              )}

              {messages.map(msg => (
                <div key={msg.id} className={`message ${msg.role}`}>
                  <div className="message-content">
                    <pre>{msg.content}</pre>

                    {msg.agentChain && (
                      <div className="agent-chain">
                        <div className="chain-title">🔗 Agent 处理链路</div>
                        {msg.agentChain.map((agent, idx) => (
                          <div key={idx} className="chain-step">
                            <span className="chain-agent">{agent.agent}</span>
                            <span className="chain-action">{agent.action}</span>
                          </div>
                        ))}
                      </div>
                    )}

                    {msg.workflowId && (
                      <div className="workflow-info">
                        <span className="task-type">{msg.taskType}</span>
                        <span className="workflow-id">
                          工作流: {msg.workflowId}
                        </span>
                        <button
                          className="view-workflow-btn"
                          onClick={() => viewWorkflow(msg.workflowId)}
                        >
                          查看详情
                        </button>
                      </div>
                    )}
                  </div>
                  <div className="message-time">{msg.timestamp}</div>
                </div>
              ))}

              {isLoading && (
                <div className="message assistant">
                  <div className="message-content loading">
                    <span className="loading-dot"></span>
                    <span className="loading-dot"></span>
                    <span className="loading-dot"></span>
                    Agent 处理中...
                  </div>
                </div>
              )}
            </div>

            {/* 输入区域 */}
            <div className="input-area">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                placeholder="请描述您的问题，例如：查询订单、申请退款、投诉建议..."
                disabled={isLoading}
              />
              <button onClick={handleSend} disabled={isLoading || !input.trim()}>
                发送
              </button>
            </div>
          </>
        )}

        {activeTab === 'orders' && (
          <div className="orders-panel">
            <h2>📦 订单列表</h2>
            <div className="orders-grid">
              {orders.map(order => (
                <div key={order.order_id} className="order-card">
                  <div className="order-header">
                    <span className="order-id">{order.order_id}</span>
                    <span className={`order-status ${order.status}`}>{order.status}</span>
                  </div>
                  <div className="order-product">{order.product_name}</div>
                  <div className="order-price">¥{order.price}</div>
                  <div className="order-shipping">
                    🚚 {order.shipping_status}
                    {order.tracking_number && <span> | {order.tracking_number}</span>}
                  </div>
                  <div className="order-actions">
                    <button onClick={() => {
                      setSelectedOrder(order.order_id)
                      setInput(`查询订单 ${order.order_id} 的状态`)
                      setActiveTab('chat')
                    }}>查询</button>
                    <button onClick={() => {
                      setSelectedOrder(order.order_id)
                      setInput(`申请订单 ${order.order_id} 退款`)
                      setActiveTab('chat')
                    }}>退款</button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'stats' && (
          <div className="stats-panel">
            <h2>📊 系统统计</h2>
            {stats && (
              <div className="stats-grid">
                <div className="stat-card">
                  <div className="stat-value">{stats.statistics?.total_workflows || 0}</div>
                  <div className="stat-label">总工作流数</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value">{stats.statistics?.completed || 0}</div>
                  <div className="stat-label">已完成</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value">{stats.statistics?.success_rate || '0%'}</div>
                  <div className="stat-label">成功率</div>
                </div>
              </div>
            )}

            {stats?.statistics?.task_type_distribution && (
              <div className="task-distribution">
                <h3>任务类型分布</h3>
                {Object.entries(stats.statistics.task_type_distribution).map(([type, count]) => (
                  <div key={type} className="distribution-item">
                    <span className="type-name">{type}</span>
                    <div className="type-bar">
                      <div
                        className="type-fill"
                        style={{ width: `${(count / stats.statistics.total_workflows) * 100}%` }}
                      ></div>
                    </div>
                    <span className="type-count">{count}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* 工作流详情弹窗 */}
        {workflowDetails && (
          <div className="workflow-modal">
            <div className="modal-content">
              <div className="modal-header">
                <h3>工作流详情</h3>
                <button onClick={() => setWorkflowDetails(null)}>✕</button>
              </div>
              <div className="modal-body">
                <p><strong>工作流ID:</strong> {workflowDetails.workflow_id}</p>
                <p><strong>任务类型:</strong> {workflowDetails.task_type}</p>
                <p><strong>状态:</strong> {workflowDetails.status}</p>

                <h4>执行步骤</h4>
                <div className="workflow-steps">
                  {workflowDetails.steps?.map((step, idx) => (
                    <div key={idx} className={`step-item ${step.status}`}>
                      <div className="step-number">{idx + 1}</div>
                      <div className="step-info">
                        <span className="step-agent">{step.agent}</span>
                        <span className="step-action">{step.action}</span>
                        <span className="step-status">{step.status}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

export default CustomerService

