import { useState, useEffect, useRef } from 'react'
import Sidebar from './components/Sidebar'
import ChatArea from './components/ChatArea'
import InputArea from './components/InputArea'
import Toast from './components/Toast'
import { checkHealth, loadTools, sendChatMessage } from './api'
import './App.css'

function App() {
  const [messages, setMessages] = useState([])
  const [sessionId, setSessionId] = useState('')
  const [tools, setTools] = useState({})
  const [isLoading, setIsLoading] = useState(false)
  const [toast, setToast] = useState({ show: false, message: '', type: 'info' })
  const [showWelcome, setShowWelcome] = useState(true)

  useEffect(() => {
    // 初始化
    initApp()
  }, [])

  const initApp = async () => {
    try {
      const healthData = await checkHealth()
      if (healthData.status === 'ok') {
        showToast('✅ 服务连接正常', 'success')
      }
    } catch (error) {
      showToast('❌ 无法连接到服务器', 'error')
    }

    try {
      const toolsData = await loadTools()
      setTools(toolsData.tools || {})
    } catch (error) {
      console.error('Failed to load tools:', error)
    }
  }

  const showToast = (message, type = 'info') => {
    setToast({ show: true, message, type })
    setTimeout(() => {
      setToast({ show: false, message: '', type: 'info' })
    }, 3000)
  }

  const handleSendMessage = async (query) => {
    if (!query.trim()) {
      showToast('请输入问题', 'error')
      return
    }

    setShowWelcome(false)

    // 添加用户消息
    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: query,
      timestamp: new Date().toLocaleTimeString()
    }
    setMessages(prev => [...prev, userMessage])

    // 添加加载消息
    const loadingMessage = {
      id: Date.now() + 1,
      role: 'assistant',
      content: '思考中...',
      isLoading: true,
      timestamp: new Date().toLocaleTimeString()
    }
    setMessages(prev => [...prev, loadingMessage])
    setIsLoading(true)

    try {
      const data = await sendChatMessage(query, sessionId)

      // 移除加载消息，添加真实回复
      setMessages(prev => {
        const filtered = prev.filter(m => !m.isLoading)
        return [...filtered, {
          id: Date.now() + 2,
          role: 'assistant',
          content: data.response,
          timestamp: new Date().toLocaleTimeString(),
          meta: {
            taskType: data.task_type,
            toolCalls: data.tool_calls,
            llmUsed: data.llm_used
          }
        }]
      })

      setSessionId(data.session_id)
    } catch (error) {
      setMessages(prev => {
        const filtered = prev.filter(m => !m.isLoading)
        return [...filtered, {
          id: Date.now() + 2,
          role: 'assistant',
          content: '网络错误，请检查服务器是否运行',
          timestamp: new Date().toLocaleTimeString()
        }]
      })
      showToast('请求失败', 'error')
    } finally {
      setIsLoading(false)
    }
  }

  const handleNewChat = () => {
    setMessages([])
    setSessionId('')
    setShowWelcome(true)
    showToast('已开始新对话')
  }

  const handleQuickQuery = (query) => {
    handleSendMessage(query)
  }

  return (
    <div className="app-container">
      <Sidebar
        tools={tools}
        onNewChat={handleNewChat}
        showToast={showToast}
      />
      <main className="main-content">
        <header className="top-bar">
          <div className="model-selector">
            <span>GPT-3.5-turbo</span>
            <span>▾</span>
          </div>
          <div className="top-actions">
            <button className="btn-secondary" onClick={initApp}>Health Check</button>
          </div>
        </header>

        <ChatArea
          messages={messages}
          showWelcome={showWelcome}
          onQuickQuery={handleQuickQuery}
        />

        <InputArea
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
        />
      </main>

      <Toast
        show={toast.show}
        message={toast.message}
        type={toast.type}
      />
    </div>
  )
}

export default App

