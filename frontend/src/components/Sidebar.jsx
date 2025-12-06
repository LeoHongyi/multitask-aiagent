import './Sidebar.css'

const toolIcons = {
  weather: '🌤️',
  news: '📰',
  search: '🔍',
  text_process: '📝'
}

function Sidebar({ tools, onNewChat, showToast }) {
  return (
    <aside className="sidebar">
      <div className="logo">
        <span className="logo-icon">◉</span>
        <span className="logo-text">AI Assistant</span>
      </div>

      <button className="new-chat-btn" onClick={onNewChat}>
        <span>⊕</span> New Chat
      </button>

      <div className="menu-section">
        <h3>Features</h3>
        <ul className="menu-list">
          <li className="active"><span>💬</span> Chat</li>
          <li><span>📁</span> Archived</li>
          <li><span>📚</span> Library</li>
        </ul>
      </div>

      <div className="menu-section">
        <h3>Tools</h3>
        <ul className="menu-list">
          {Object.entries(tools).map(([name, description]) => (
            <li
              key={name}
              onClick={() => showToast(`工具: ${name} - ${description}`)}
              title={description}
            >
              <span>{toolIcons[name] || '🔧'}</span> {name}
            </li>
          ))}
        </ul>
      </div>

      <div className="sidebar-footer">
        <div className="upgrade-card">
          <span className="upgrade-icon">💎</span>
          <h4>Upgrade to premium</h4>
          <p>Boost productivity with seamless automation and responsive AI.</p>
          <button className="upgrade-btn">Upgrade</button>
        </div>
      </div>
    </aside>
  )
}

export default Sidebar

