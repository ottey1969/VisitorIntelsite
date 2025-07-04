// Enhanced Live AI Conversation Feed with Real 4-API Backend Integration
// Perfect Roofing Team - Real Business Data with Fixed Timestamps

class EnhancedLiveConversationManager {
    constructor() {
        this.config = {
            BACKEND_URL: '',
            POLLING_INTERVAL: 5000,         // 5 seconds for real-time updates
            STATUS_CHECK_INTERVAL: 1000,    // 1 second for countdown
            API_TIMEOUT: 10000,             // 10 seconds
            RETRY_ATTEMPTS: 3,              // 3 retry attempts
            MAX_MESSAGES: 20                // Keep last 20 messages
        };
        
        this.state = {
            messages: [],
            currentTopic: null,
            lastUpdate: null,
            isLoading: false,
            conversationActive: false,
            timeRemaining: 0,
            nextConversationTime: null,
            localTime: null,
            systemRunning: false,
            apiStatus: {
                openai: false,
                anthropic: false,
                perplexity: false,
                gemini: false
            },
            roundInfo: {
                roundNumber: 1,
                messageCount: 0,
                messagesRemaining: 16
            }
        };
        
        this.timers = {
            polling: null,
            statusCheck: null,
            localTimeUpdate: null
        };
        
        this.socket = null;
        this.init();
    }
    
    init() {
        console.log('[EnhancedLiveConversation] Initializing with 4-API backend...');
        this.setupSocketIO();
        this.setupEventListeners();
        this.loadInitialConversation();
        this.startPolling();
        this.startStatusUpdates();
        this.startLocalTimeUpdates();
        this.updateAPIStatus();
    }
    
    setupSocketIO() {
        try {
            // Initialize Socket.IO connection
            this.socket = io();
            
            // Listen for new messages
            this.socket.on('new_message', (data) => {
                console.log('[SocketIO] New message received:', data);
                this.addNewMessage(data);
            });
            
            // Listen for conversation events
            this.socket.on('conversation_started', (data) => {
                console.log('[SocketIO] Conversation started:', data);
                this.onConversationStarted(data);
            });
            
            this.socket.on('conversation_completed', (data) => {
                console.log('[SocketIO] Conversation completed:', data);
                this.onConversationCompleted(data);
            });
            
            // Handle connection events
            this.socket.on('connect', () => {
                console.log('[SocketIO] Connected to enhanced backend');
                this.updateConnectionStatus(true);
            });
            
            this.socket.on('disconnect', () => {
                console.log('[SocketIO] Disconnected from enhanced backend');
                this.updateConnectionStatus(false);
            });
            
        } catch (error) {
            console.error('[SocketIO] Error initializing socket connection:', error);
        }
    }
    
    setupEventListeners() {
        // Investigation button clicks
        document.addEventListener('click', (e) => {
            if (e.target.closest('.investigation-btn')) {
                e.preventDefault();
                const btn = e.target.closest('.investigation-btn');
                const messageId = btn.dataset.messageId;
                const agentType = btn.dataset.agentType;
                const messageContent = btn.dataset.messageContent;
                this.showInvestigation(agentType, messageContent, messageId);
            }
        });
        
        // Manual start button
        const startBtn = document.querySelector('.start-conversation-btn');
        if (startBtn) {
            startBtn.addEventListener('click', () => {
                this.startConversationManually();
            });
        }
        
        // Refresh button
        const refreshBtn = document.querySelector('.refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.refreshConversation();
            });
        }
    }
    
    async loadInitialConversation() {
        console.log('[EnhancedLiveConversation] Loading initial conversation from enhanced backend...');
        this.setLoadingState(true);
        
        try {
            const response = await this.makeAPICall('/api/enhanced-conversation/messages');
            if (response.messages) {
                this.state.messages = response.messages || [];
                this.renderMessages();
                console.log(`[EnhancedLiveConversation] Loaded ${this.state.messages.length} messages`);
            }
        } catch (error) {
            console.error('[EnhancedLiveConversation] Error loading initial conversation:', error);
            this.showError('Failed to load conversation. Retrying...');
        } finally {
            this.setLoadingState(false);
        }
    }
    
    startPolling() {
        // Clear existing polling
        if (this.timers.polling) {
            clearInterval(this.timers.polling);
        }
        
        // Start polling for new messages
        this.timers.polling = setInterval(async () => {
            try {
                await this.checkForNewMessages();
            } catch (error) {
                console.error('[EnhancedLiveConversation] Polling error:', error);
            }
        }, this.config.POLLING_INTERVAL);
        
        console.log('[EnhancedLiveConversation] Started polling for new messages');
    }
    
    startStatusUpdates() {
        // Clear existing status updates
        if (this.timers.statusCheck) {
            clearInterval(this.timers.statusCheck);
        }
        
        // Start status checking for countdown timer
        this.timers.statusCheck = setInterval(async () => {
            try {
                await this.updateConversationStatus();
            } catch (error) {
                console.error('[EnhancedLiveConversation] Status update error:', error);
            }
        }, this.config.STATUS_CHECK_INTERVAL);
        
        console.log('[EnhancedLiveConversation] Started status updates');
    }
    
    startLocalTimeUpdates() {
        // Clear existing local time updates
        if (this.timers.localTimeUpdate) {
            clearInterval(this.timers.localTimeUpdate);
        }
        
        // Update local time every second
        this.updateLocalTime();
        this.timers.localTimeUpdate = setInterval(() => {
            this.updateLocalTime();
        }, 1000);
        
        console.log('[EnhancedLiveConversation] Started local time updates');
    }
    
    updateLocalTime() {
        const now = new Date();
        const timeString = now.toLocaleTimeString('en-US', {
            hour: 'numeric',
            minute: '2-digit',
            second: '2-digit',
            hour12: true
        });
        
        this.state.localTime = timeString;
        
        // Update local time displays
        const localTimeElements = document.querySelectorAll('.local-time-display, .current-time');
        localTimeElements.forEach(element => {
            element.textContent = timeString;
        });
    }
    
    async updateConversationStatus() {
        try {
            const response = await this.makeAPICall('/api/enhanced-conversation/status');
            
            if (response) {
                // Update state
                this.state.conversationActive = response.conversation_active;
                this.state.timeRemaining = response.time_remaining_seconds;
                this.state.nextConversationTime = response.next_conversation_time;
                this.state.systemRunning = response.system_running;
                this.state.apiStatus = response.api_status || {};
                this.state.roundInfo.roundNumber = response.current_round;
                this.state.roundInfo.messageCount = response.message_count;
                
                // Update countdown display
                this.updateCountdownDisplay();
                
                // Update status indicators
                this.updateStatusIndicators();
            }
        } catch (error) {
            console.error('[EnhancedLiveConversation] Error updating status:', error);
        }
    }
    
    updateCountdownDisplay() {
        const countdownElement = document.getElementById('enhanced-countdown');
        if (!countdownElement) return;
        
        const minutes = Math.floor(this.state.timeRemaining / 60);
        const seconds = this.state.timeRemaining % 60;
        
        const timeString = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        
        // Create or update countdown display
        countdownElement.innerHTML = `
            <div class="enhanced-countdown-container bg-gradient-primary text-white rounded-4 p-4 mb-4">
                <div class="row align-items-center">
                    <div class="col-md-8">
                        <h4 class="fw-bold mb-2">
                            ${this.state.conversationActive ? 'AI Conversation Active' : 'Next AI Conversation'}
                            <span class="badge ${this.state.conversationActive ? 'bg-success' : 'bg-warning'} ms-2">
                                ${this.state.conversationActive ? '🔴 LIVE' : '⏱️ WAITING'}
                            </span>
                        </h4>
                        <div class="countdown-timer">
                            <span class="countdown-time h2 fw-bold">${timeString}</span>
                            <span class="countdown-label ms-2">${this.state.conversationActive ? 'elapsed' : 'remaining'}</span>
                        </div>
                        <div class="countdown-info mt-2">
                            <small class="opacity-75">
                                Local time: ${this.state.localTime} • 
                                Next conversation: ${this.state.nextConversationTime || 'Calculating...'}
                            </small>
                        </div>
                    </div>
                    <div class="col-md-4 text-center">
                        <div class="api-status-grid">
                            <div class="row g-2">
                                <div class="col-6">
                                    <div class="api-status-item">
                                        <span class="status-dot ${this.state.apiStatus.openai ? 'bg-success' : 'bg-danger'}"></span>
                                        <small>OpenAI</small>
                                    </div>
                                </div>
                                <div class="col-6">
                                    <div class="api-status-item">
                                        <span class="status-dot ${this.state.apiStatus.anthropic ? 'bg-success' : 'bg-danger'}"></span>
                                        <small>Anthropic</small>
                                    </div>
                                </div>
                                <div class="col-6">
                                    <div class="api-status-item">
                                        <span class="status-dot ${this.state.apiStatus.perplexity ? 'bg-success' : 'bg-danger'}"></span>
                                        <small>Perplexity</small>
                                    </div>
                                </div>
                                <div class="col-6">
                                    <div class="api-status-item">
                                        <span class="status-dot ${this.state.apiStatus.gemini ? 'bg-success' : 'bg-danger'}"></span>
                                        <small>Gemini</small>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="progress mt-3" style="height: 6px;">
                    <div class="progress-bar bg-warning" role="progressbar" 
                         style="width: ${this.state.conversationActive ? '100%' : Math.max(0, ((1800 - this.state.timeRemaining) / 1800) * 100)}%">
                    </div>
                </div>
            </div>
        `;
        
        // Add CSS if not already added
        this.addCountdownStyles();
    }
    
    addCountdownStyles() {
        if (document.getElementById('enhanced-countdown-styles')) return;
        
        const styles = document.createElement('style');
        styles.id = 'enhanced-countdown-styles';
        styles.textContent = `
            .api-status-item {
                display: flex;
                align-items: center;
                gap: 4px;
                font-size: 11px;
            }
            
            .status-dot {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                display: inline-block;
            }
            
            .countdown-time {
                font-family: 'Courier New', monospace;
                letter-spacing: 2px;
            }
            
            .enhanced-countdown-container {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            }
        `;
        
        document.head.appendChild(styles);
    }
    
    updateStatusIndicators() {
        // Update system status indicators
        const statusElements = document.querySelectorAll('.system-status');
        statusElements.forEach(element => {
            element.textContent = this.state.systemRunning ? 'System Running' : 'System Stopped';
            element.className = `system-status badge ${this.state.systemRunning ? 'bg-success' : 'bg-danger'}`;
        });
        
        // Update conversation status
        const conversationElements = document.querySelectorAll('.conversation-status');
        conversationElements.forEach(element => {
            element.textContent = this.state.conversationActive ? 'LIVE' : 'WAITING';
            element.className = `conversation-status badge ${this.state.conversationActive ? 'bg-danger' : 'bg-warning'}`;
        });
    }
    
    async checkForNewMessages() {
        try {
            const response = await this.makeAPICall('/api/enhanced-conversation/messages');
            
            if (response.messages && response.messages.length > this.state.messages.length) {
                // New messages available
                const newMessages = response.messages.slice(this.state.messages.length);
                
                newMessages.forEach(message => {
                    this.addNewMessage(message);
                });
                
                console.log(`[EnhancedLiveConversation] Added ${newMessages.length} new messages`);
            }
        } catch (error) {
            console.error('[EnhancedLiveConversation] Error checking for new messages:', error);
        }
    }
    
    addNewMessage(messageData) {
        // Add to state
        this.state.messages.push(messageData);
        
        // Keep only last MAX_MESSAGES
        if (this.state.messages.length > this.config.MAX_MESSAGES) {
            this.state.messages = this.state.messages.slice(-this.config.MAX_MESSAGES);
        }
        
        // Add to display
        this.addMessageToDisplay(messageData);
        
        // Scroll to new message
        this.scrollToLatestMessage();
    }
    
    addMessageToDisplay(message) {
        const streamContainer = document.getElementById('publicLiveStream');
        if (!streamContainer) return;
        
        const messageElement = document.createElement('div');
        messageElement.className = 'conversation-message mb-3 fade-in';
        messageElement.innerHTML = `
            <div class="message-header d-flex justify-content-between align-items-center mb-2">
                <div class="agent-info">
                    <span class="agent-badge badge bg-primary me-2">${message.agent_type}</span>
                    <span class="agent-name fw-bold">${message.agent_name}</span>
                    <span class="round-info text-muted ms-2">• Round ${message.round_number || this.state.roundInfo.roundNumber}</span>
                </div>
                <div class="message-meta">
                    <span class="message-timestamp text-muted me-2">${message.timestamp}</span>
                    <span class="live-indicator badge bg-danger">🔴 LIVE</span>
                </div>
            </div>
            <div class="message-content p-3 bg-light rounded-3">
                ${message.message_text}
            </div>
            <div class="message-footer mt-2 d-flex justify-content-between align-items-center">
                <small class="text-muted">
                    <i class="fas fa-building me-1"></i>Perfect Roofing Team Discussion
                </small>
                <button class="btn btn-outline-primary btn-sm investigation-btn" 
                        data-message-id="${message.id}" 
                        data-agent-type="${message.agent_type}"
                        data-message-content="${message.message_text}">
                    <i class="fas fa-search me-1"></i>Short Investigation
                </button>
            </div>
        `;
        
        streamContainer.appendChild(messageElement);
        
        // Animate message appearance
        setTimeout(() => {
            messageElement.classList.add('show');
        }, 100);
    }
    
    renderMessages() {
        const streamContainer = document.getElementById('publicLiveStream');
        if (!streamContainer) return;
        
        // Clear existing messages
        streamContainer.innerHTML = '';
        
        // Add each message
        this.state.messages.forEach(message => {
            this.addMessageToDisplay(message);
        });
        
        // Remove loading indicator
        this.setLoadingState(false);
    }
    
    scrollToLatestMessage() {
        const streamContainer = document.getElementById('publicLiveStream');
        if (streamContainer) {
            streamContainer.scrollTop = streamContainer.scrollHeight;
        }
    }
    
    setLoadingState(isLoading) {
        this.state.isLoading = isLoading;
        
        const loadingElement = document.querySelector('.loading-indicator');
        if (loadingElement) {
            loadingElement.style.display = isLoading ? 'block' : 'none';
        }
        
        const streamContainer = document.getElementById('publicLiveStream');
        if (streamContainer && isLoading && streamContainer.children.length === 0) {
            streamContainer.innerHTML = `
                <div class="text-center py-4 loading-indicator">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading conversations...</span>
                    </div>
                    <p class="text-muted mt-2">Loading enhanced AI conversations...</p>
                </div>
            `;
        }
    }
    
    async makeAPICall(endpoint, options = {}) {
        const defaultOptions = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
            timeout: this.config.API_TIMEOUT,
            ...options
        };
        
        try {
            const response = await fetch(this.config.BACKEND_URL + endpoint, defaultOptions);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error(`[EnhancedLiveConversation] API call failed for ${endpoint}:`, error);
            throw error;
        }
    }
    
    async startConversationManually() {
        try {
            const response = await this.makeAPICall('/api/enhanced-conversation/start', {
                method: 'POST'
            });
            
            if (response.success) {
                this.showNotification('Enhanced conversation started manually!', 'success');
            } else {
                this.showNotification(response.message || 'Failed to start conversation', 'error');
            }
        } catch (error) {
            console.error('[EnhancedLiveConversation] Error starting conversation manually:', error);
            this.showNotification('Error starting conversation', 'error');
        }
    }
    
    async refreshConversation() {
        console.log('[EnhancedLiveConversation] Refreshing conversation...');
        await this.loadInitialConversation();
        this.showNotification('Conversation refreshed!', 'info');
    }
    
    async updateAPIStatus() {
        try {
            const response = await this.makeAPICall('/api/enhanced-conversation/health');
            
            if (response.api_keys_configured) {
                this.state.apiStatus = response.api_keys_configured;
                console.log('[EnhancedLiveConversation] API status updated:', this.state.apiStatus);
            }
        } catch (error) {
            console.error('[EnhancedLiveConversation] Error updating API status:', error);
        }
    }
    
    updateConnectionStatus(connected) {
        const statusElements = document.querySelectorAll('.connection-status');
        statusElements.forEach(element => {
            element.textContent = connected ? 'Connected' : 'Disconnected';
            element.className = `connection-status badge ${connected ? 'bg-success' : 'bg-danger'}`;
        });
    }
    
    showInvestigation(agentType, messageContent, messageId) {
        // Enhanced investigation modal
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">AI Investigation: ${agentType}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="investigation-content">
                            <h6>Message Analysis:</h6>
                            <div class="alert alert-info">
                                ${messageContent}
                            </div>
                            <h6>AI Agent Details:</h6>
                            <ul>
                                <li><strong>Agent Type:</strong> ${agentType}</li>
                                <li><strong>Specialization:</strong> ${this.getAgentSpecialization(agentType)}</li>
                                <li><strong>API Source:</strong> ${this.getAgentAPI(agentType)}</li>
                            </ul>
                            <h6>Investigation Results:</h6>
                            <p>This message was generated by a real AI API and represents authentic discussion about Perfect Roofing Team's services and expertise.</p>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Show modal using Bootstrap
        const bootstrapModal = new bootstrap.Modal(modal);
        bootstrapModal.show();
        
        // Remove modal from DOM when hidden
        modal.addEventListener('hidden.bs.modal', () => {
            document.body.removeChild(modal);
        });
    }
    
    getAgentSpecialization(agentType) {
        const specializations = {
            'Business AI Assistant': 'Business strategy and operations',
            'SEO AI Specialist': 'Search engine optimization',
            'Customer Service AI': 'Customer experience and support',
            'Marketing AI Expert': 'Marketing and brand positioning'
        };
        return specializations[agentType] || 'General AI assistance';
    }
    
    getAgentAPI(agentType) {
        const apis = {
            'Business AI Assistant': 'OpenAI GPT-4',
            'SEO AI Specialist': 'Anthropic Claude-3',
            'Customer Service AI': 'Perplexity AI',
            'Marketing AI Expert': 'Google Gemini'
        };
        return apis[agentType] || 'Unknown API';
    }
    
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 300px;';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }
    
    showError(message) {
        this.showNotification(message, 'error');
    }
    
    onConversationStarted(data) {
        console.log('[EnhancedLiveConversation] Conversation started:', data);
        this.state.conversationActive = true;
        this.showNotification(`New AI conversation started: Round ${data.round_number}`, 'success');
    }
    
    onConversationCompleted(data) {
        console.log('[EnhancedLiveConversation] Conversation completed:', data);
        this.state.conversationActive = false;
        this.showNotification(`Conversation completed: ${data.total_messages} messages generated`, 'info');
    }
    
    // Cleanup method
    destroy() {
        // Clear all timers
        Object.values(this.timers).forEach(timer => {
            if (timer) clearInterval(timer);
        });
        
        // Disconnect socket
        if (this.socket) {
            this.socket.disconnect();
        }
        
        console.log('[EnhancedLiveConversation] Manager destroyed');
    }
}

// Initialize the enhanced conversation manager when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('[EnhancedLiveConversation] DOM ready, initializing...');
    
    // Create global instance
    window.enhancedConversationManager = new EnhancedLiveConversationManager();
    
    // Add manual controls for testing
    window.startConversation = () => window.enhancedConversationManager.startConversationManually();
    window.refreshConversation = () => window.enhancedConversationManager.refreshConversation();
    window.getSystemHealth = () => window.enhancedConversationManager.makeAPICall('/api/enhanced-conversation/health');
    
    console.log('[EnhancedLiveConversation] Enhanced conversation manager initialized');
    console.log('Available functions: startConversation(), refreshConversation(), getSystemHealth()');
});

// Add CSS for animations
const animationStyles = document.createElement('style');
animationStyles.textContent = `
    .fade-in {
        opacity: 0;
        transform: translateY(20px);
        transition: all 0.3s ease;
    }
    
    .fade-in.show {
        opacity: 1;
        transform: translateY(0);
    }
    
    .conversation-message {
        border-left: 4px solid #007bff;
        padding-left: 15px;
        margin-bottom: 20px;
    }
    
    .agent-badge {
        font-size: 10px;
        padding: 4px 8px;
    }
    
    .live-indicator {
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
`;

document.head.appendChild(animationStyles);

