/**
 * LLM Integration JavaScript
 * Handles chat, code generation, and code fixing
 */

const API_BASE = '';
let chatHistory = [];

// ============================================================================
// Tab Management
// ============================================================================

function switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active class from all buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(tabName).classList.add('active');
    
    // Add active class to clicked button
    event.target.classList.add('active');
}

// ============================================================================
// LLM Status Check
// ============================================================================

async function checkLLMStatus() {
    try {
        const response = await fetch(`${API_BASE}/api/llm/status`);
        const data = await response.json();
        
        const statusBadge = document.getElementById('llm-status');
        const icon = statusBadge.querySelector('.status-icon');
        const text = statusBadge.querySelector('span:last-child');
        
        if (data.available) {
            icon.textContent = '🟢';
            text.textContent = `LLM: ${data.model}`;
        } else {
            icon.textContent = '🔴';
            text.textContent = 'LLM: Offline';
        }
    } catch (error) {
        console.error('Failed to check LLM status:', error);
        const statusBadge = document.getElementById('llm-status');
        const icon = statusBadge.querySelector('.status-icon');
        const text = statusBadge.querySelector('span:last-child');
        icon.textContent = '🔴';
        text.textContent = 'LLM: Error';
    }
}

// ============================================================================
// Chat Functions
// ============================================================================

function addChatMessage(role, content, isLoading = false) {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${role}`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = role === 'user' ? '👤' : '🤖';
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    
    if (isLoading) {
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'message-loading';
        loadingDiv.innerHTML = '<div class="loading-dot"></div><div class="loading-dot"></div><div class="loading-dot"></div>';
        messageContent.appendChild(loadingDiv);
        messageDiv.id = 'loading-message';
    } else {
        const name = document.createElement('strong');
        name.textContent = role === 'user' ? 'You' : 'ESP32 Assistant';
        
        const text = document.createElement('p');
        // Convert markdown-style code blocks to HTML
        let formattedContent = content
            .replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
        text.innerHTML = formattedContent;
        
        messageContent.appendChild(name);
        messageContent.appendChild(text);
    }
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(messageContent);
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return messageDiv;
}

function removeLoadingMessage() {
    const loadingMsg = document.getElementById('loading-message');
    if (loadingMsg) {
        loadingMsg.remove();
    }
}

async function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Add user message
    addChatMessage('user', message);
    chatHistory.push({ role: 'user', content: message });
    
    // Clear input
    input.value = '';
    
    // Show loading
    addChatMessage('assistant', '', true);
    
    const sendBtn = document.getElementById('send-btn');
    sendBtn.classList.add('loading');
    sendBtn.disabled = true;
    
    try {
        const temperature = parseInt(document.getElementById('chat-temperature').value) / 100;
        
        const response = await fetch(`${API_BASE}/api/llm/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                temperature: temperature
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Remove loading message
        removeLoadingMessage();
        
        // Add assistant response
        addChatMessage('assistant', data.response);
        chatHistory.push({ role: 'assistant', content: data.response });
        
    } catch (error) {
        console.error('Chat error:', error);
        removeLoadingMessage();
        addChatMessage('assistant', '❌ Sorry, I encountered an error. Please make sure the LLM service is running and try again.');
    } finally {
        sendBtn.classList.remove('loading');
        sendBtn.disabled = false;
    }
}

function sendQuickQuestion(question) {
    document.getElementById('chat-input').value = question;
    sendChatMessage();
}

function clearChat() {
    const chatMessages = document.getElementById('chat-messages');
    chatMessages.innerHTML = `
        <div class="chat-message assistant">
            <div class="message-avatar">🤖</div>
            <div class="message-content">
                <strong>ESP32 Assistant</strong>
                <p>Hello! I'm your ESP32 development assistant powered by Qwen2.5-Coder. Ask me anything about ESP32 development, ESP-IDF, hardware interfacing, or embedded C programming.</p>
            </div>
        </div>
    `;
    chatHistory = [];
}

// ============================================================================
// Code Generation
// ============================================================================

async function generateCode() {
    const description = document.getElementById('code-description').value.trim();
    
    if (!description) {
        alert('Please describe what code you want to generate');
        return;
    }
    
    const language = document.getElementById('code-language').value;
    const framework = document.getElementById('code-framework').value;
    const temperature = parseFloat(document.getElementById('gen-temperature').value);
    
    const btn = event.target;
    btn.classList.add('loading');
    btn.disabled = true;
    
    // Show loading in output
    document.getElementById('code-output').innerHTML = '<pre><code>// Generating code...\n// This may take a moment...\n\n⏳ Please wait...</code></pre>';
    document.getElementById('code-explanation').textContent = 'Generating explanation...';
    
    try {
        const response = await fetch(`${API_BASE}/api/llm/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                description: description,
                language: language,
                framework: framework,
                temperature: temperature
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Display generated code
        document.getElementById('code-output').innerHTML = `<pre><code>${escapeHtml(data.code)}</code></pre>`;
        document.getElementById('code-explanation').textContent = data.explanation;
        
    } catch (error) {
        console.error('Code generation error:', error);
        document.getElementById('code-output').innerHTML = '<pre><code>❌ Failed to generate code.\nPlease check that the LLM service is running and try again.</code></pre>';
        document.getElementById('code-explanation').textContent = 'Error: ' + error.message;
    } finally {
        btn.classList.remove('loading');
        btn.disabled = false;
    }
}

function copyGeneratedCode() {
    const codeOutput = document.getElementById('code-output');
    const code = codeOutput.querySelector('code').textContent;
    
    navigator.clipboard.writeText(code).then(() => {
        const btn = document.getElementById('copy-code-btn');
        const originalText = btn.textContent;
        btn.textContent = '✅ Copied!';
        setTimeout(() => {
            btn.textContent = originalText;
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy:', err);
        alert('Failed to copy code to clipboard');
    });
}

// ============================================================================
// Code Fixing
// ============================================================================

async function fixCode() {
    const buggyCode = document.getElementById('buggy-code').value.trim();
    const errorMessage = document.getElementById('error-message').value.trim();
    
    if (!buggyCode || !errorMessage) {
        alert('Please provide both the buggy code and error message');
        return;
    }
    
    const filename = document.getElementById('fix-filename').value;
    const component = document.getElementById('fix-component').value;
    
    const btn = event.target;
    btn.classList.add('loading');
    btn.disabled = true;
    
    // Show loading status
    const fixStatus = document.getElementById('fix-status');
    fixStatus.className = 'fix-status';
    fixStatus.innerHTML = `
        <div class="status-icon">⏳</div>
        <div class="status-text">Analyzing code and fixing...</div>
    `;
    
    document.getElementById('fix-result').style.display = 'none';
    
    try {
        const response = await fetch(`${API_BASE}/api/llm/fix`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                buggy_code: buggyCode,
                error_message: errorMessage,
                filename: filename,
                component: component
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            // Show success status
            fixStatus.className = 'fix-status success';
            fixStatus.innerHTML = `
                <div class="status-icon">✅</div>
                <div class="status-text">Code fixed successfully!</div>
            `;
            
            // Show results
            document.getElementById('fix-result').style.display = 'block';
            
            // Diagnosis
            document.getElementById('fix-diagnosis').innerHTML = `
                <p>${escapeHtml(data.diagnosis)}</p>
                <p style="margin-top: 10px;">
                    <span class="confidence-badge confidence-${data.confidence}">${data.confidence} confidence</span>
                </p>
            `;
            
            // Changes
            if (data.changes_made && data.changes_made.length > 0) {
                const changesList = data.changes_made.map(change => `<li>${escapeHtml(change)}</li>`).join('');
                document.getElementById('fix-changes').innerHTML = `<ul>${changesList}</ul>`;
            } else {
                document.getElementById('fix-changes').innerHTML = '<p style="color: #b0b0b0;">No specific changes listed</p>';
            }
            
            // Fixed code
            document.getElementById('fixed-code-output').innerHTML = `<pre><code>${escapeHtml(data.fixed_code)}</code></pre>`;
            
        } else {
            // Show error status
            fixStatus.className = 'fix-status error';
            fixStatus.innerHTML = `
                <div class="status-icon">❌</div>
                <div class="status-text">Failed to fix code</div>
            `;
            
            document.getElementById('fix-result').style.display = 'block';
            document.getElementById('fix-diagnosis').innerHTML = `<p>${escapeHtml(data.diagnosis || 'Unknown error occurred')}</p>`;
            document.getElementById('fix-changes').innerHTML = '<p style="color: #f44336;">No changes made</p>';
        }
        
    } catch (error) {
        console.error('Code fix error:', error);
        fixStatus.className = 'fix-status error';
        fixStatus.innerHTML = `
            <div class="status-icon">❌</div>
            <div class="status-text">Error: ${escapeHtml(error.message)}</div>
        `;
    } finally {
        btn.classList.remove('loading');
        btn.disabled = false;
    }
}

function copyFixedCode() {
    const codeOutput = document.getElementById('fixed-code-output');
    const code = codeOutput.querySelector('code').textContent;
    
    navigator.clipboard.writeText(code).then(() => {
        const btn = event.target;
        const originalText = btn.textContent;
        btn.textContent = '✅ Copied!';
        setTimeout(() => {
            btn.textContent = originalText;
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy:', err);
        alert('Failed to copy code to clipboard');
    });
}

// ============================================================================
// Utilities
// ============================================================================

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

// ============================================================================
// Initialize
// ============================================================================

// Check LLM status on load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', checkLLMStatus);
} else {
    checkLLMStatus();
}

// Check LLM status every 30 seconds
setInterval(checkLLMStatus, 30000);

// Add enter key handler for chat
document.addEventListener('DOMContentLoaded', () => {
    const chatInput = document.getElementById('chat-input');
    if (chatInput) {
        chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendChatMessage();
            }
        });
    }
});

console.log('🤖 LLM Integration loaded');
