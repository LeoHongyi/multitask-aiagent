// API 基础地址
const API_BASE = 'http://localhost:8000';

// 当前会话 ID
let sessionId = '';

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', () => {
    checkHealth();
    loadTools();
});

// 健康检查
async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        const data = await response.json();

        if (data.status === 'ok') {
            showToast('✅ 服务连接正常', 'success');
        } else {
            showToast('⚠️ 服务状态异常', 'error');
        }
        console.log('Health check:', data);
    } catch (error) {
        showToast('❌ 无法连接到服务器', 'error');
        console.error('Health check failed:', error);
    }
}

// 加载可用工具
async function loadTools() {
    try {
        const response = await fetch(`${API_BASE}/api/tools`);
        const data = await response.json();

        const toolsList = document.getElementById('tools-list');
        if (toolsList && data.tools) {
            toolsList.innerHTML = '';
            const icons = {
                'weather': '🌤️',
                'news': '📰',
                'search': '🔍',
                'text_process': '📝'
            };

            Object.entries(data.tools).forEach(([name, description]) => {
                const li = document.createElement('li');
                li.innerHTML = `<span>${icons[name] || '🔧'}</span> ${name}`;
                li.title = description;
                li.onclick = () => showToast(`工具: ${name} - ${description}`);
                toolsList.appendChild(li);
            });
        }
        console.log('Available tools:', data.tools);
    } catch (error) {
        console.error('Failed to load tools:', error);
    }
}

// 发送消息
async function sendMessage() {
    const input = document.getElementById('query-input');
    const query = input.value.trim();

    if (!query) {
        showToast('请输入问题', 'error');
        return;
    }

    // 隐藏欢迎区域
    const welcomeSection = document.getElementById('welcome-section');
    if (welcomeSection) {
        welcomeSection.style.display = 'none';
    }

    // 添加用户消息
    addMessage(query, 'user');
    input.value = '';

    // 添加加载状态
    const loadingId = addMessage('<span class="loading">思考中</span>', 'assistant', true);

    try {
        const response = await fetch(`${API_BASE}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: query,
                session_id: sessionId || '',
                context: ''
            })
        });

        const data = await response.json();

        // 移除加载消息
        removeMessage(loadingId);

        if (response.ok) {
            // 保存会话 ID
            sessionId = data.session_id;

            // 添加助手回复
            addMessage(data.response, 'assistant', false, {
                taskType: data.task_type,
                toolCalls: data.tool_calls,
                llmUsed: data.llm_used
            });

            console.log('Chat response:', data);
        } else {
            addMessage(`错误: ${data.detail || '请求失败'}`, 'assistant');
            showToast('请求失败', 'error');
        }
    } catch (error) {
        removeMessage(loadingId);
        addMessage('网络错误，请检查服务器是否运行', 'assistant');
        showToast('网络错误', 'error');
        console.error('Chat error:', error);
    }
}

// 快速查询
function quickQuery(query) {
    document.getElementById('query-input').value = query;
    sendMessage();
}

// 添加消息到聊天区域
function addMessage(content, role, isLoading = false, meta = null) {
    const container = document.getElementById('messages-container');
    const messageId = 'msg-' + Date.now();

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    messageDiv.id = messageId;

    let metaHtml = '';
    if (meta) {
        metaHtml = `
            <div class="tool-info">
                <span class="tool-badge">${meta.taskType || 'QA'}</span>
                ${meta.llmUsed ? '<span class="tool-badge">LLM</span>' : ''}
                ${meta.toolCalls && meta.toolCalls.length > 0 ? 
                    meta.toolCalls.map(tc => `<span class="tool-badge">${tc.tool_name}</span>`).join('') : ''}
            </div>
        `;
    }

    messageDiv.innerHTML = `
        <div class="message-content">
            ${formatMessage(content)}
            ${metaHtml}
        </div>
        <div class="message-meta">${new Date().toLocaleTimeString()}</div>
    `;

    container.appendChild(messageDiv);

    // 滚动到底部
    container.scrollTop = container.scrollHeight;

    return messageId;
}

// 移除消息
function removeMessage(messageId) {
    const message = document.getElementById(messageId);
    if (message) {
        message.remove();
    }
}

// 格式化消息内容
function formatMessage(content) {
    // 转换换行符
    let formatted = content.replace(/\n/g, '<br>');

    // 简单的 Markdown 支持
    // 粗体
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // 斜体
    formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
    // 代码
    formatted = formatted.replace(/`(.*?)`/g, '<code>$1</code>');

    return formatted;
}

// 处理回车键
function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

// 显示 Toast 提示
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast show ${type}`;

    setTimeout(() => {
        toast.className = 'toast';
    }, 3000);
}

// 新建对话
function newChat() {
    sessionId = '';
    document.getElementById('messages-container').innerHTML = '';
    document.getElementById('welcome-section').style.display = 'block';
    showToast('已开始新对话');
}

// 绑定新建对话按钮
document.querySelector('.new-chat-btn')?.addEventListener('click', newChat);

