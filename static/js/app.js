// Travel Guide AI Assistant - Frontend JavaScript

// DOM Elements
const apiStatus = document.getElementById('api-status');
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');
const clearBtn = document.getElementById('clear-btn');

// No model information needed for simplified interface

// Application state
let isApiValid = false;
let chatHistory = [];
let sessionId = generateSessionId(); // Generate unique session ID for this conversation
// Default settings - no need for user selection
const selectedModel = 'gemini-1.5-pro-latest';
const selectedRole = 'Tourist';

// Generate a random session ID
function generateSessionId() {
    return 'session_' + Math.random().toString(36).substring(2, 15);
}

// Initialize the application
function init() {
    setupEventListeners();
    // Auto-validate API key on load
    validateApiKey();
}

// Set up event listeners
function setupEventListeners() {
    // Send message
    sendBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    // Clear chat
    clearBtn.addEventListener('click', clearChat);
}

// Validate the API key
async function validateApiKey() {
    apiStatus.innerHTML = '';
    apiStatus.classList.remove('status-success', 'status-error');
    
    try {
        const response = await fetch('/api/validate-key');
        const data = await response.json();
        
        if (data.success) {
            // Don't show success message, just enable the chat
            apiStatus.innerHTML = '';
            isApiValid = true;
            
            // Enable chat
            chatInput.disabled = false;
            sendBtn.disabled = false;
        } else {
            // Only show error messages
            apiStatus.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${data.error}`;
            apiStatus.classList.add('status-error');
            isApiValid = false;
        }
    } catch (error) {
        apiStatus.innerHTML = '<i class="fas fa-exclamation-circle"></i> Connection failed';
        apiStatus.classList.add('status-error');
        isApiValid = false;
    }
}

// Send a message to the API
async function sendMessage() {
    const message = chatInput.value.trim();
    
    if (!message || !isApiValid) {
        return;
    }
    
    // Add user message to chat
    addMessage(message, 'user');
    chatInput.value = '';
    
    // Show typing indicator
    const typingIndicator = document.createElement('div');
    typingIndicator.className = 'typing-indicator';
    typingIndicator.innerHTML = '<span></span><span></span><span></span>';
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
                session_id: sessionId, // Send session ID for conversation tracking
                chat_history: chatHistory // Send chat history
            })
        });
        
        const data = await response.json();
        
        // Remove typing indicator
        typingIndicator.remove();
        
        if (data.success) {
            // Add assistant message to chat
            addMessage(data.response, 'assistant');
            
            // If there's a new session ID, update it
            if (data.session_id) {
                sessionId = data.session_id;
            }
        } else {
            // Show error message
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-message';
            errorDiv.textContent = `Error: ${data.error}`;
            chatMessages.appendChild(errorDiv);
        }
    } catch (error) {
        // Remove typing indicator
        typingIndicator.remove();
        
        // Show error message
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = `Error: ${error.message}`;
        chatMessages.appendChild(errorDiv);
    }
    
    scrollToBottom();
}

// Add a message to the chat
function addMessage(content, role) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role === 'user' ? 'user-message' : 'bot-message'}`;
    
    // Convert URLs to links and preserve line breaks
    const formattedContent = content
        .replace(/https?:\/\/[^\s]+/g, url => `<a href="${url}" target="_blank">${url}</a>`)
        .replace(/\n/g, '<br>');
    
    messageDiv.innerHTML = role === 'user' ? `<span>${formattedContent}</span>` : formattedContent;
    
    // Add action buttons for bot messages
    if (role === 'assistant') {
        const actionsDiv = document.createElement('div');
        actionsDiv.className = 'message-actions';
        
        // Copy button
        const copyBtn = document.createElement('button');
        copyBtn.className = 'action-btn';
        copyBtn.innerHTML = '<i class="fas fa-copy"></i>Copy';
        copyBtn.onclick = () => {
            navigator.clipboard.writeText(content);
            copyBtn.innerHTML = '<i class="fas fa-check"></i>Copied!';
            setTimeout(() => {
                copyBtn.innerHTML = '<i class="fas fa-copy"></i>Copy';
            }, 2000);
        };
        
        // Speak button
        const speakBtn = document.createElement('button');
        speakBtn.className = 'action-btn';
        speakBtn.innerHTML = '<i class="fas fa-volume-up"></i>Speak';
        speakBtn.onclick = () => {
            if (speechSynthesis.speaking) {
                speechSynthesis.cancel();
                speakBtn.innerHTML = '<i class="fas fa-volume-up"></i>Speak';
            } else {
                const utterance = new SpeechSynthesisUtterance(content);
                utterance.lang = 'en-US';
                speechSynthesis.speak(utterance);
                speakBtn.innerHTML = '<i class="fas fa-volume-mute"></i>Stop';
                
                utterance.onend = () => {
                    speakBtn.innerHTML = '<i class="fas fa-volume-up"></i>Speak';
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
    // Keep only the welcome message
    chatMessages.innerHTML = `
        <div class="welcome-message">
            <h2>Welcome to Bharat Guide</h2>
            <p>Ask your India travel questions below</p>
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