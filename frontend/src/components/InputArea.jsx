import { useState } from 'react'
import './InputArea.css'

function InputArea({ onSendMessage, isLoading }) {
  const [query, setQuery] = useState('')

  const handleSubmit = () => {
    if (query.trim() && !isLoading) {
      onSendMessage(query)
      setQuery('')
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="input-section">
      <div className="input-container">
        <div className="input-wrapper">
          <span className="input-icon">✨</span>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask Anything..."
            disabled={isLoading}
          />
        </div>
        <div className="input-actions">
          <button className="action-btn" title="Attach">📎</button>
          <button className="action-btn" title="Settings">⚙️</button>
          <button
            className="send-btn"
            onClick={handleSubmit}
            disabled={isLoading || !query.trim()}
          >
            <span>↑</span>
          </button>
        </div>
      </div>
    </div>
  )
}

export default InputArea

