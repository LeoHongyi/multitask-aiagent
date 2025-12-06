import './ChatArea.css'

function ChatArea({ messages, showWelcome, onQuickQuery }) {
  const formatMessage = (content) => {
    if (!content) return '';
    return content
      .replace(/\n/g, '<br>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`(.*?)`/g, '<code>$1</code>');
  }

  return (
    <div className="chat-container">
      {showWelcome && (
        <div className="welcome-section">
          <div className="welcome-icon">🤖</div>
          <h1>Ready to Create Something New?</h1>
          <div className="quick-actions">
            <button className="quick-btn" onClick={() => onQuickQuery('北京天气怎么样')}>
              <span>🌤️</span> 查询天气
            </button>
            <button className="quick-btn" onClick={() => onQuickQuery('最新科技新闻')}>
              <span>📰</span> 获取新闻
            </button>
            <button className="quick-btn" onClick={() => onQuickQuery('搜索人工智能')}>
              <span>🔍</span> 搜索信息
            </button>
          </div>
        </div>
      )}

      <div className="messages-container">
        {messages.map((message) => (
          <div key={message.id} className={`message ${message.role}`}>
            <div className="message-content">
              {message.isLoading ? (
                <span className="loading">思考中</span>
              ) : (
                <div dangerouslySetInnerHTML={{ __html: formatMessage(message.content) }} />
              )}

              {message.meta && (
                <div className="tool-info">
                  <span className="tool-badge">{message.meta.taskType || 'QA'}</span>
                  {message.meta.llmUsed && <span className="tool-badge">LLM</span>}
                  {message.meta.toolCalls?.map((tc, idx) => (
                    <span key={idx} className="tool-badge">{tc.tool_name}</span>
                  ))}
                </div>
              )}
            </div>
            <div className="message-meta">{message.timestamp}</div>
          </div>
        ))}
      </div>

      {!showWelcome && messages.length === 0 && (
        <div className="empty-state">开始新的对话吧</div>
      )}

      {showWelcome && (
        <div className="feature-cards">
          <div className="feature-card" onClick={() => onQuickQuery('北京今天天气如何')}>
            <div className="card-header">
              <span className="card-icon">🌤️</span>
              <span className="card-tag">Weather</span>
            </div>
            <h3>天气查询</h3>
            <p>获取全球城市的实时天气信息</p>
          </div>
          <div className="feature-card" onClick={() => onQuickQuery('最新科技新闻有哪些')}>
            <div className="card-header">
              <span className="card-icon">📰</span>
              <span className="card-tag">News</span>
            </div>
            <h3>新闻资讯</h3>
            <p>获取最新的科技、时事新闻</p>
          </div>
          <div className="feature-card" onClick={() => onQuickQuery('什么是机器学习')}>
            <div className="card-header">
              <span className="card-icon">💻</span>
              <span className="card-tag">Q&A</span>
            </div>
            <h3>智能问答</h3>
            <p>回答各种问题，提供专业解答</p>
          </div>
        </div>
      )}
    </div>
  )
}

export default ChatArea

