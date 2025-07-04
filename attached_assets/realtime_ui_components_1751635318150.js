/**
 * Real-Time UI Components for Enhanced 4-API Conversation System
 * ============================================================
 * 
 * Features:
 * - Countdown timer between conversations
 * - Real-time message updates with unpredictable timing
 * - WebSocket integration for live updates
 * - Professional user experience
 * - Mobile-responsive design
 */

class EnhancedConversationUI {
    constructor() {
        this.socket = null;
        this.countdownInterval = null;
        this.currentState = 'waiting';
        this.conversationId = null;
        this.messageCount = 0;
        
        this.init();
    }
    
    init() {
        this.setupWebSocket();
        this.setupUI();
        this.startStatusUpdates();
        
        console.log('Enhanced Conversation UI initialized');
    }
    
    setupWebSocket() {
        // Initialize WebSocket connection
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        try {
            this.socket = new WebSocket(wsUrl);
            
            this.socket.onopen = () => {
                console.log('WebSocket connected');
                this.updateConnectionStatus(true);
            };
            
            this.socket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            };
            
            this.socket.onclose = () => {
                console.log('WebSocket disconnected');
                this.updateConnectionStatus(false);
                // Attempt to reconnect after 5 seconds
                setTimeout(() => this.setupWebSocket(), 5000);
            };
            
            this.socket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateConnectionStatus(false);
            };
            
        } catch (error) {
            console.error('Failed to setup WebSocket:', error);
            // Fallback to polling if WebSocket fails
            this.setupPolling();
        }
    }
    
    setupPolling() {
        // Fallback polling mechanism
        setInterval(() => {
            this.fetchSystemStatus();
        }, 5000); // Poll every 5 seconds
    }
    
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'new_message':
                this.addNewMessage(data.message);
                break;
            case 'countdown_update':
                this.updateCountdown(data.countdown);
                break;
            case 'state_change':
                this.handleStateChange(data.state);
                break;
            case 'conversation_start':
                this.handleConversationStart(data.conversation);
                break;
            case 'conversation_complete':
                this.handleConversationComplete(data.conversation);
                break;
            default:
                console.log('Unknown message type:', data.type);
        }
    }
    
    setupUI() {
        // Create main UI structure if it doesn't exist
        if (!document.getElementById('enhanced-conversation-container')) {
            this.createUIStructure();
        }
        
        this.bindEventListeners();
        this.fetchSystemStatus();
    }
    
    createUIStructure() {
        const container = document.createElement('div');
        container.id = 'enhanced-conversation-container';
        container.innerHTML = `
            <div class="conversation-header">
                <div class="status-indicator">
                    <span class="status-dot" id="status-dot"></span>
                    <span class="status-text" id="status-text">Initializing...</span>
                </div>
                <div class="connection-status" id="connection-status">
                    <span class="connection-dot"></span>
                    <span class="connection-text">Connecting...</span>
                </div>
            </div>
            
            <div class="countdown-section" id="countdown-section">
                <div class="countdown-display">
                    <div class="countdown-timer" id="countdown-timer">--:--</div>
                    <div class="countdown-message" id="countdown-message">Loading...</div>
                </div>
                <div class="countdown-progress">
                    <div class="progress-bar" id="progress-bar"></div>
                </div>
            </div>
            
            <div class="conversation-section" id="conversation-section">
                <div class="conversation-info">
                    <h3>Perfect Roofing Team <span class="live-badge">LIVE</span></h3>
                    <div class="conversation-stats">
                        <span class="stat">
                            <span class="stat-number" id="total-messages">0</span>
                            <span class="stat-label">AI messages today</span>
                        </span>
                        <span class="stat">
                            <span class="stat-number">4</span>
                            <span class="stat-label">AI Agents Active</span>
                        </span>
                        <span class="stat">
                            <span class="stat-number">24/7</span>
                            <span class="stat-label">Real-time Generation</span>
                        </span>
                    </div>
                </div>
                
                <div class="messages-container" id="messages-container">
                    <!-- Messages will be dynamically added here -->
                </div>
                
                <div class="conversation-footer">
                    <div class="api-indicators">
                        <div class="api-indicator" data-api="openai">
                            <span class="api-dot"></span>
                            <span class="api-name">OpenAI GPT-4</span>
                        </div>
                        <div class="api-indicator" data-api="anthropic">
                            <span class="api-dot"></span>
                            <span class="api-name">Anthropic Claude-3</span>
                        </div>
                        <div class="api-indicator" data-api="perplexity">
                            <span class="api-dot"></span>
                            <span class="api-name">Perplexity AI</span>
                        </div>
                        <div class="api-indicator" data-api="gemini">
                            <span class="api-dot"></span>
                            <span class="api-name">Google Gemini</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Insert into existing conversation area or append to body
        const existingContainer = document.querySelector('.conversation-container') || 
                                document.querySelector('#conversation-area') ||
                                document.body;
        
        existingContainer.appendChild(container);
        
        // Add CSS styles
        this.addStyles();
    }
    
    addStyles() {
        const styles = `
            <style>
            #enhanced-conversation-container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }
            
            .conversation-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
                padding: 15px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 12px;
                color: white;
            }
            
            .status-indicator {
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .status-dot {
                width: 12px;
                height: 12px;
                border-radius: 50%;
                background: #4ade80;
                animation: pulse 2s infinite;
            }
            
            .status-dot.waiting {
                background: #fbbf24;
            }
            
            .status-dot.active {
                background: #4ade80;
            }
            
            .status-dot.error {
                background: #ef4444;
            }
            
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
            
            .connection-status {
                display: flex;
                align-items: center;
                gap: 8px;
                font-size: 14px;
            }
            
            .connection-dot {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: #4ade80;
            }
            
            .connection-dot.disconnected {
                background: #ef4444;
            }
            
            .countdown-section {
                background: white;
                border-radius: 12px;
                padding: 30px;
                margin-bottom: 20px;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                text-align: center;
            }
            
            .countdown-timer {
                font-size: 48px;
                font-weight: bold;
                color: #1f2937;
                margin-bottom: 10px;
                font-family: 'Courier New', monospace;
            }
            
            .countdown-message {
                font-size: 18px;
                color: #6b7280;
                margin-bottom: 20px;
            }
            
            .countdown-progress {
                width: 100%;
                height: 8px;
                background: #e5e7eb;
                border-radius: 4px;
                overflow: hidden;
            }
            
            .progress-bar {
                height: 100%;
                background: linear-gradient(90deg, #3b82f6, #8b5cf6);
                border-radius: 4px;
                transition: width 1s ease-in-out;
            }
            
            .conversation-section {
                background: white;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            }
            
            .conversation-info {
                padding: 20px;
                background: linear-gradient(135deg, #1e40af 0%, #3730a3 100%);
                color: white;
            }
            
            .conversation-info h3 {
                margin: 0 0 15px 0;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            .live-badge {
                background: #ef4444;
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
                animation: pulse 2s infinite;
            }
            
            .conversation-stats {
                display: flex;
                gap: 30px;
                flex-wrap: wrap;
            }
            
            .stat {
                display: flex;
                flex-direction: column;
                align-items: center;
            }
            
            .stat-number {
                font-size: 24px;
                font-weight: bold;
                color: #60a5fa;
            }
            
            .stat-label {
                font-size: 12px;
                opacity: 0.8;
            }
            
            .messages-container {
                max-height: 600px;
                overflow-y: auto;
                padding: 20px;
            }
            
            .message {
                display: flex;
                align-items: flex-start;
                gap: 15px;
                margin-bottom: 20px;
                padding: 15px;
                border-radius: 12px;
                background: #f8fafc;
                border-left: 4px solid #3b82f6;
                animation: slideIn 0.5s ease-out;
            }
            
            @keyframes slideIn {
                from {
                    opacity: 0;
                    transform: translateY(20px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            .message.new {
                background: #ecfdf5;
                border-left-color: #10b981;
            }
            
            .agent-avatar {
                width: 40px;
                height: 40px;
                border-radius: 50%;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: bold;
                font-size: 14px;
                flex-shrink: 0;
            }
            
            .message-content {
                flex: 1;
            }
            
            .message-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 8px;
            }
            
            .agent-name {
                font-weight: 600;
                color: #1f2937;
            }
            
            .message-time {
                font-size: 12px;
                color: #6b7280;
                display: flex;
                align-items: center;
                gap: 5px;
            }
            
            .live-indicator {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: #ef4444;
                animation: pulse 1s infinite;
            }
            
            .message-text {
                color: #374151;
                line-height: 1.5;
            }
            
            .conversation-footer {
                padding: 20px;
                background: #f9fafb;
                border-top: 1px solid #e5e7eb;
            }
            
            .api-indicators {
                display: flex;
                justify-content: space-around;
                flex-wrap: wrap;
                gap: 15px;
            }
            
            .api-indicator {
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 8px 12px;
                background: white;
                border-radius: 8px;
                border: 1px solid #e5e7eb;
            }
            
            .api-dot {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: #10b981;
            }
            
            .api-dot.inactive {
                background: #6b7280;
            }
            
            .api-name {
                font-size: 12px;
                font-weight: 500;
                color: #374151;
            }
            
            /* Mobile responsive */
            @media (max-width: 768px) {
                #enhanced-conversation-container {
                    padding: 10px;
                }
                
                .conversation-header {
                    flex-direction: column;
                    gap: 10px;
                    text-align: center;
                }
                
                .countdown-timer {
                    font-size: 36px;
                }
                
                .conversation-stats {
                    justify-content: center;
                    gap: 20px;
                }
                
                .api-indicators {
                    justify-content: center;
                }
                
                .message {
                    flex-direction: column;
                    gap: 10px;
                }
                
                .message-header {
                    flex-direction: column;
                    align-items: flex-start;
                    gap: 5px;
                }
            }
            </style>
        `;
        
        if (!document.getElementById('enhanced-conversation-styles')) {
            const styleElement = document.createElement('div');
            styleElement.id = 'enhanced-conversation-styles';
            styleElement.innerHTML = styles;
            document.head.appendChild(styleElement);
        }
    }
    
    bindEventListeners() {
        // Add any interactive event listeners here
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                // Page became visible, refresh status
                this.fetchSystemStatus();
            }
        });
    }
    
    startStatusUpdates() {
        // Update countdown every second
        this.countdownInterval = setInterval(() => {
            this.updateCountdownDisplay();
        }, 1000);
        
        // Fetch system status every 30 seconds
        setInterval(() => {
            this.fetchSystemStatus();
        }, 30000);
    }
    
    async fetchSystemStatus() {
        try {
            const response = await fetch('/api/enhanced-status');
            const status = await response.json();
            
            this.updateSystemStatus(status);
            
        } catch (error) {
            console.error('Failed to fetch system status:', error);
            this.updateConnectionStatus(false);
        }
    }
    
    updateSystemStatus(status) {
        this.currentState = status.current_state || 'waiting';
        this.conversationId = status.current_conversation_id;
        
        // Update status indicator
        const statusDot = document.getElementById('status-dot');
        const statusText = document.getElementById('status-text');
        
        if (statusDot && statusText) {
            statusDot.className = `status-dot ${this.currentState}`;
            
            switch (this.currentState) {
                case 'waiting':
                    statusText.textContent = 'Waiting for next conversation';
                    break;
                case 'active':
                    statusText.textContent = 'Live conversation in progress';
                    break;
                case 'completed':
                    statusText.textContent = 'Conversation completed';
                    break;
                default:
                    statusText.textContent = 'System status unknown';
            }
        }
        
        // Update countdown
        if (status.countdown_info) {
            this.updateCountdown(status.countdown_info);
        }
        
        // Update stats
        this.updateStats(status);
        
        // Update API indicators
        this.updateAPIIndicators(status.api_status);
    }
    
    updateCountdown(countdownInfo) {
        const countdownSection = document.getElementById('countdown-section');
        const conversationSection = document.getElementById('conversation-section');
        
        if (countdownInfo.state === 'waiting') {
            // Show countdown
            if (countdownSection) countdownSection.style.display = 'block';
            if (conversationSection) conversationSection.style.display = 'none';
            
            this.updateCountdownDisplay(countdownInfo);
            
        } else if (countdownInfo.state === 'active') {
            // Show conversation
            if (countdownSection) countdownSection.style.display = 'none';
            if (conversationSection) conversationSection.style.display = 'block';
            
        } else if (countdownInfo.state === 'starting') {
            // Show starting message
            const countdownMessage = document.getElementById('countdown-message');
            if (countdownMessage) {
                countdownMessage.textContent = 'Conversation starting now...';
            }
        }
    }
    
    updateCountdownDisplay(countdownInfo = null) {
        const timerElement = document.getElementById('countdown-timer');
        const messageElement = document.getElementById('countdown-message');
        const progressBar = document.getElementById('progress-bar');
        
        if (!timerElement || !messageElement) return;
        
        if (countdownInfo && countdownInfo.total_seconds !== undefined) {
            const totalSeconds = countdownInfo.total_seconds;
            const minutes = Math.floor(totalSeconds / 60);
            const seconds = totalSeconds % 60;
            
            timerElement.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            messageElement.textContent = countdownInfo.message;
            
            // Update progress bar (30 minutes = 1800 seconds)
            const progressPercent = Math.max(0, Math.min(100, ((1800 - totalSeconds) / 1800) * 100));
            if (progressBar) {
                progressBar.style.width = `${progressPercent}%`;
            }
        }
    }
    
    updateStats(status) {
        const totalMessagesElement = document.getElementById('total-messages');
        if (totalMessagesElement && status.total_messages !== undefined) {
            totalMessagesElement.textContent = status.total_messages;
        }
    }
    
    updateAPIIndicators(apiStatus) {
        if (!apiStatus) return;
        
        Object.keys(apiStatus).forEach(api => {
            const indicator = document.querySelector(`[data-api="${api}"] .api-dot`);
            if (indicator) {
                indicator.className = apiStatus[api] ? 'api-dot' : 'api-dot inactive';
            }
        });
    }
    
    updateConnectionStatus(connected) {
        const connectionDot = document.querySelector('.connection-dot');
        const connectionText = document.querySelector('.connection-text');
        
        if (connectionDot) {
            connectionDot.className = connected ? 'connection-dot' : 'connection-dot disconnected';
        }
        
        if (connectionText) {
            connectionText.textContent = connected ? 'Connected' : 'Disconnected';
        }
    }
    
    addNewMessage(messageData) {
        const messagesContainer = document.getElementById('messages-container');
        if (!messagesContainer) return;
        
        const messageElement = document.createElement('div');
        messageElement.className = 'message new';
        
        // Get agent initials for avatar
        const initials = messageData.agent_name
            .split(' ')
            .map(word => word[0])
            .join('')
            .toUpperCase();
        
        messageElement.innerHTML = `
            <div class="agent-avatar">${initials}</div>
            <div class="message-content">
                <div class="message-header">
                    <span class="agent-name">${messageData.agent_name}</span>
                    <div class="message-time">
                        <span class="live-indicator"></span>
                        <span>${messageData.display_time}</span>
                        <span class="live-text">LIVE</span>
                    </div>
                </div>
                <div class="message-text">${messageData.message_content}</div>
            </div>
        `;
        
        messagesContainer.appendChild(messageElement);
        
        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        // Remove 'new' class after animation
        setTimeout(() => {
            messageElement.classList.remove('new');
        }, 500);
        
        // Keep only last 20 messages for performance
        const messages = messagesContainer.querySelectorAll('.message');
        if (messages.length > 20) {
            messages[0].remove();
        }
        
        this.messageCount++;
    }
    
    handleStateChange(newState) {
        this.currentState = newState;
        this.fetchSystemStatus(); // Refresh full status
    }
    
    handleConversationStart(conversationData) {
        this.conversationId = conversationData.id;
        this.currentState = 'active';
        
        // Clear existing messages
        const messagesContainer = document.getElementById('messages-container');
        if (messagesContainer) {
            messagesContainer.innerHTML = '';
        }
        
        // Show conversation section
        this.updateCountdown({ state: 'active' });
    }
    
    handleConversationComplete(conversationData) {
        this.currentState = 'completed';
        
        // Show completion message briefly, then switch to countdown
        setTimeout(() => {
            this.fetchSystemStatus();
        }, 3000);
    }
    
    destroy() {
        if (this.socket) {
            this.socket.close();
        }
        
        if (this.countdownInterval) {
            clearInterval(this.countdownInterval);
        }
        
        const container = document.getElementById('enhanced-conversation-container');
        if (container) {
            container.remove();
        }
        
        const styles = document.getElementById('enhanced-conversation-styles');
        if (styles) {
            styles.remove();
        }
    }
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.enhancedConversationUI = new EnhancedConversationUI();
});

// Export for manual initialization
window.EnhancedConversationUI = EnhancedConversationUI;

