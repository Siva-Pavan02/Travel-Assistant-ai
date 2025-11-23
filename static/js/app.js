// Guide Me - AI Travel Assistant
// Frontend JavaScript with ChatGPT-style formatting

const logger = {
    info: (msg) => console.log(`[INFO] ${msg}`),
    error: (msg) => console.error(`[ERROR] ${msg}`),
    warn: (msg) => console.warn(`[WARN] ${msg}`)
};

// DOM Elements
const apiStatus = document.getElementById('api-status');
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');
const newChatBtn = document.querySelector('.new-chat-btn');

// Application State
let isApiValid = true;  // Changed default to true to allow chat submission
let chatHistory = [];
let sessionId = generateSessionId();
const selectedModel = 'gemini-pro-latest';
const selectedRole = 'Tourist';

function generateSessionId() {
    return 'session_' + Math.random().toString(36).substring(2, 15);
}

function init() {
    setupEventListeners();
    validateApiKey();
}

function setupEventListeners() {
    sendBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    if (newChatBtn) {
        newChatBtn.addEventListener('click', clearChat);
    }
}

// Set a message in the input field (for quick prompts)
function setMessage(text) {
    chatInput.value = text;
    chatInput.focus();
}

// Validate the API key
async function validateApiKey() {
    apiStatus.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Validating API...';
    apiStatus.classList.remove('status-success', 'status-error');
    
    try {
        const response = await fetch('/api/validate-key');
        const data = await response.json();
        
        if (data.success) {
            logger.info('API key validated successfully');
            apiStatus.innerHTML = '';
            isApiValid = true;
        } else {
            const errorMsg = data.error || 'API key validation failed';
            logger.error(`API validation failed: ${errorMsg}`);
            apiStatus.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${escapeHtml(errorMsg)}`;
            apiStatus.classList.add('status-error');
            isApiValid = true;
        }
    } catch (error) {
        logger.error(`Connection failed: ${error.message}`);
        apiStatus.innerHTML = '<i class="fas fa-exclamation-circle"></i> Connection error - enabling anyway';
        apiStatus.classList.add('status-error');
        isApiValid = true;
    }
}

// Escape HTML special characters to prevent XSS
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

// Format text with ChatGPT-style markdown support
function formatMessageText(text) {
    let html = escapeHtml(text);
    
    // Remove excessive line breaks - normalize triple+ line breaks to double
    html = html.replace(/\n{3,}/g, '\n\n');
    
    // Code blocks (```language...```)
    html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (match, language, code) => {
        const lang = language || 'text';
        return `<pre class="code-block"><div class="code-header">${lang}</div><code>${code.trim()}</code></pre>`;
    });
    
    // Inline code (`code`)
    html = html.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');
    
    // Bold (**text**)
    html = html.replace(/\*\*([^\*]+)\*\*/g, '<strong>$1</strong>');
    
    // Italic (*text*)
    html = html.replace(/\*([^\*]+)\*/g, '<em>$1</em>');
    
    // Links with proper color
    html = html.replace(/https?:\/\/[^\s<]+/g, url => 
        `<a href="${url}" target="_blank" rel="noopener noreferrer">→ ${url}</a>`
    );
    
    // Headers (# Text) - process before line breaks
    html = html.replace(/^### (.+)$/gm, '<h3 class="message-header">$1</h3>');
    html = html.replace(/^## (.+)$/gm, '<h2 class="message-header">$1</h2>');
    html = html.replace(/^# (.+)$/gm, '<h1 class="message-header">$1</h1>');
    
    // Bullet lists (- item)
    html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
    
    // Group consecutive list items
    html = html.replace(/(<li>[\s\S]*?<\/li>)/g, (match) => {
        if (!match.includes('<ul') && !match.includes('<ol')) {
            return '<ul class="message-list">' + match + '</ul>';
        }
        return match;
    });
    
    // Numbered lists (1. item, 2. item, etc)
    html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');
    
    // Double line breaks become paragraph separators
    html = html.replace(/\n\n/g, '</p><p>');
    html = '<p>' + html + '</p>';
    
    // Single line breaks within paragraphs become br
    html = html.replace(/<p>([^<]*?)\n([^<]*?)<\/p>/g, (match, p1, p2) => {
        return `<p>${p1}<br>${p2}</p>`;
    });
    
    // Clean up empty paragraphs
    html = html.replace(/<p><\/p>/g, '');
    html = html.replace(/<p>\s*<(h[1-3]|ul|ol|pre)/g, '<$1');
    html = html.replace(/<\/(h[1-3]|ul|ol|pre)>\s*<\/p>/g, '</$1>');
    
    return html;
}

// Send a message to the API
async function sendMessage() {
    const message = chatInput.value.trim();
    
    if (!message || !isApiValid) {
        return;
    }
    
    // Clear input
    chatInput.value = '';
    
    // Remove welcome section if first message
    const welcomeSection = document.querySelector('.welcome-section');
    if (welcomeSection) {
        welcomeSection.remove();
    }
    
    // Add user message to chat
    addMessage(message, 'user');
    
    // Show typing indicator
    const typingIndicator = document.createElement('div');
    typingIndicator.className = 'message bot-message';
    typingIndicator.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
    chatMessages.appendChild(typingIndicator);
    scrollToBottom();
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                role: selectedRole,
                model: selectedModel,
                session_id: sessionId,
                chat_history: chatHistory
            })
        });
        
        const data = await response.json();
        
        // Remove typing indicator
        typingIndicator.remove();
        
        if (data.success || data.message) {
            // Add assistant message to chat
            addMessage(data.response || data.message, 'bot');
            
            // Update session ID if provided
            if (data.session_id) {
                sessionId = data.session_id;
            }
        } else {
            // Show error message
            const errorMessage = data.error || 'An error occurred. Please try again.';
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-message';
            errorDiv.textContent = `Error: ${errorMessage}`;
            chatMessages.appendChild(errorDiv);
            logger.error(`Chat error: ${errorMessage}`);
        }
    } catch (error) {
        // Remove typing indicator
        typingIndicator.remove();
        
        // Show error message
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = `Error: ${error.message || 'Failed to connect to the server'}`;
        chatMessages.appendChild(errorDiv);
        logger.error(`Chat exception: ${error.message}`);
    }
    
    scrollToBottom();
}

// Add a message to the chat
function addMessage(content, role) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role === 'user' ? 'user-message' : 'bot-message'}`;
    
    if (role === 'user') {
        // User messages are plain text
        const textSpan = document.createElement('span');
        textSpan.textContent = content;
        messageDiv.appendChild(textSpan);
    } else {
        // Bot messages with formatted content
        const contentDiv = document.createElement('div');
        contentDiv.innerHTML = formatMessageText(content);
        messageDiv.appendChild(contentDiv);
        
        // Add action buttons for bot messages
        const actionsDiv = document.createElement('div');
        actionsDiv.className = 'message-actions';
        
        // Copy button
        const copyBtn = document.createElement('button');
        copyBtn.className = 'action-btn';
        copyBtn.innerHTML = '<i class="fas fa-copy"></i> Copy';
        copyBtn.onclick = () => {
            navigator.clipboard.writeText(content);
            copyBtn.innerHTML = '<i class="fas fa-check"></i> Copied!';
            setTimeout(() => {
                copyBtn.innerHTML = '<i class="fas fa-copy"></i> Copy';
            }, 2000);
        };
        
        // Speak button
        const speakBtn = document.createElement('button');
        speakBtn.className = 'action-btn';
        speakBtn.innerHTML = '<i class="fas fa-volume-up"></i> Speak';
        speakBtn.onclick = () => {
            if (speechSynthesis.speaking) {
                speechSynthesis.cancel();
                speakBtn.innerHTML = '<i class="fas fa-volume-up"></i> Speak';
            } else {
                const utterance = new SpeechSynthesisUtterance(content);
                utterance.lang = 'en-US';
                speechSynthesis.speak(utterance);
                speakBtn.innerHTML = '<i class="fas fa-volume-mute"></i> Stop';
                
                utterance.onend = () => {
                    speakBtn.innerHTML = '<i class="fas fa-volume-up"></i> Speak';
                };
            }
        };
        
        actionsDiv.appendChild(copyBtn);
        actionsDiv.appendChild(speakBtn);
        messageDiv.appendChild(actionsDiv);
    }
    
    chatMessages.appendChild(messageDiv);
    
    // Add to chat history
    chatHistory.push({ role, content });
    
    scrollToBottom();
}

// Clear the chat
function clearChat() {
    // Clear messages
    chatMessages.innerHTML = `
        <div class="welcome-section">
            <div class="welcome-icon">
                <i class="fas fa-compass"></i>
            </div>
            <h2>Welcome to Guide Me</h2>
            <p>Your personal AI guide to exploring incredible India</p>
            
            <div class="quick-prompts">
                <button class="quick-prompt" onclick="setMessage('Tell me about the best time to visit India')">
                    <i class="fas fa-calendar"></i>
                    Best time to visit
                </button>
                <button class="quick-prompt" onclick="setMessage('What are the must-visit destinations in India?')">
                    <i class="fas fa-map-pin"></i>
                    Must-visit places
                </button>
                <button class="quick-prompt" onclick="setMessage('Tell me about Indian cuisine and food')">
                    <i class="fas fa-utensils"></i>
                    Indian cuisine
                </button>
                <button class="quick-prompt" onclick="setMessage('What are the transport options in India?')">
                    <i class="fas fa-train"></i>
                    Transport guide
                </button>
            </div>
        </div>
    `;
    
    // Reset chat history and generate new session ID
    chatHistory = [];
    sessionId = generateSessionId();
}

// Scroll to the bottom of the chat
function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Initialize the application
init();