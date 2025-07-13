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
            // Initialize Socket.IO connection if available
            if (typeof io !== 'undefined') {
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
            } else {
                console.log('[SocketIO] Socket.IO not available, using polling only');
            }
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
        const timeString = now.toISOString().substr(11, 8) + ' UTC';
        
        this.state.localTime = timeString;
        
        // Update UTC time displays
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
        
        const style = document.createElement('style');
        style.id = 'enhanced-countdown-styles';
        style.textContent = `
            .api-status-item {
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 4px;
                padding: 4px 8px;
                background: rgba(255,255,255,0.1);
                border-radius: 8px;
                font-size: 0.75rem;
            }
            .status-dot {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                display: inline-block;
            }
            .countdown-time {
                font-family: 'Courier New', monospace;
                font-size: 2rem;
                color: #ffc107;
            }
            .enhanced-countdown-container {
                border: 2px solid rgba(255,255,255,0.2);
                background: linear-gradient(135deg, #0d6efd 0%, #6f42c1 100%);
            }
        `;
        document.head.appendChild(style);
    }
    
    async checkForNewMessages() {
        try {
            const response = await this.makeAPICall('/api/enhanced-conversation/messages');
            if (response.messages) {
                const newMessages = response.messages || [];
                if (newMessages.length > this.state.messages.length) {
                    this.state.messages = newMessages;
                    this.renderMessages();
                }
            }
        } catch (error) {
            console.error('[EnhancedLiveConversation] Error checking for new messages:', error);
        }
    }
    
    async startConversationManually() {
        try {
            const response = await this.makeAPICall('/api/enhanced-conversation/start', 'POST');
            if (response.success) {
                console.log('[EnhancedLiveConversation] Conversation started manually');
                this.showSuccess('Enhanced conversation started successfully!');
            } else {
                this.showError(response.message || 'Failed to start conversation');
            }
        } catch (error) {
            console.error('[EnhancedLiveConversation] Error starting conversation:', error);
            this.showError('Failed to start conversation');
        }
    }
    
    async makeAPICall(endpoint, method = 'GET', data = null) {
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            },
            timeout: this.config.API_TIMEOUT
        };
        
        if (data) {
            options.body = JSON.stringify(data);
        }
        
        const response = await fetch(this.config.BACKEND_URL + endpoint, options);
        
        if (!response.ok) {
            throw new Error(`API call failed: ${response.status}`);
        }
        
        return await response.json();
    }
    
    renderMessages() {
        const container = document.getElementById('publicLiveStream');
        if (!container) return;
        
        if (this.state.messages.length === 0) {
            container.innerHTML = `
                <div class="text-center py-4">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading enhanced conversations...</span>
                    </div>
                    <p class="text-muted mt-2">Connecting to enhanced 4-API conversation system...</p>
                </div>
            `;
            return;
        }
        
        const messagesHTML = this.state.messages.map((msg, index) => `
            <div class="message-item mb-3 animate__animated animate__fadeInUp" style="animation-delay: ${index * 0.1}s">
                <div class="d-flex align-items-start">
                    <div class="agent-avatar me-3">
                        <div class="avatar ${this.getAgentColorClass(msg.agent_type)}">
                            ${this.getAgentIcon(msg.agent_type)}
                        </div>
                    </div>
                    <div class="message-content flex-grow-1">
                        <div class="message-header d-flex justify-content-between align-items-center mb-2">
                            <h6 class="agent-name mb-0">
                                <span class="text-primary fw-bold">${msg.agent_name}</span>
                                <small class="text-muted ms-2">${msg.agent_type.toUpperCase()}</small>
                            </h6>
                            <div class="message-meta">
                                <small class="text-muted">${msg.timestamp}</small>
                                <button class="btn btn-sm btn-outline-info ms-2 investigation-btn" 
                                        data-message-id="${msg.id}" 
                                        data-agent-type="${msg.agent_type}" 
                                        data-message-content="${msg.message_text || msg.content}">
                                    <i class="fas fa-search"></i> Investigate
                                </button>
                            </div>
                        </div>
                        <div class="message-text">
                            <p class="mb-0">${msg.message_text || msg.content}</p>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
        
        container.innerHTML = messagesHTML;
        
        // Auto-scroll to bottom
        container.scrollTop = container.scrollHeight;
        
        // Update conversation status
        this.updateConversationIndicators();
    }
    
    getAgentColorClass(agentType) {
        const colors = {
            'openai': 'bg-success',
            'anthropic': 'bg-warning',
            'perplexity': 'bg-info',
            'gemini': 'bg-primary'
        };
        return colors[agentType] || 'bg-secondary';
    }
    
    getAgentIcon(agentType) {
        const icons = {
            'openai': '<i class="fas fa-robot"></i>',
            'anthropic': '<i class="fas fa-brain"></i>',
            'perplexity': '<i class="fas fa-search"></i>',
            'gemini': '<i class="fas fa-star"></i>'
        };
        return icons[agentType] || '<i class="fas fa-comment"></i>';
    }
    
    updateConversationIndicators() {
        // Update live indicators
        const statusElements = document.querySelectorAll('.conversation-status');
        statusElements.forEach(element => {
            if (this.state.conversationActive) {
                element.textContent = 'LIVE';
                element.className = 'conversation-status badge bg-success';
            } else {
                element.textContent = 'WAITING';
                element.className = 'conversation-status badge bg-warning';
            }
        });
    }
    
    updateStatusIndicators() {
        // Update system status
        const systemStatus = document.querySelector('.system-status');
        if (systemStatus) {
            if (this.state.systemRunning) {
                systemStatus.textContent = 'System Running';
                systemStatus.className = 'system-status badge bg-success';
            } else {
                systemStatus.textContent = 'System Offline';
                systemStatus.className = 'system-status badge bg-danger';
            }
        }
        
        // Update connection status
        const connectionStatus = document.querySelector('.connection-status');
        if (connectionStatus) {
            if (this.socket && this.socket.connected) {
                connectionStatus.textContent = 'Connected';
                connectionStatus.className = 'connection-status badge bg-success';
            } else {
                connectionStatus.textContent = 'Polling';
                connectionStatus.className = 'connection-status badge bg-warning';
            }
        }
    }
    
    updateConnectionStatus(connected) {
        const connectionStatus = document.querySelector('.connection-status');
        if (connectionStatus) {
            if (connected) {
                connectionStatus.textContent = 'Connected';
                connectionStatus.className = 'connection-status badge bg-success';
            } else {
                connectionStatus.textContent = 'Disconnected';
                connectionStatus.className = 'connection-status badge bg-danger';
            }
        }
    }
    
    setLoadingState(loading) {
        this.state.isLoading = loading;
        const container = document.getElementById('publicLiveStream');
        if (!container) return;
        
        if (loading) {
            container.innerHTML = `
                <div class="text-center py-4 loading-indicator">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading enhanced conversations...</span>
                    </div>
                    <p class="text-muted mt-2">Connecting to enhanced 4-API conversation system...</p>
                </div>
            `;
        }
    }
    
    showError(message) {
        console.error('[EnhancedLiveConversation] Error:', message);
        // You can add toast notifications here if needed
    }
    
    showSuccess(message) {
        console.log('[EnhancedLiveConversation] Success:', message);
        // You can add toast notifications here if needed
    }
    
    // Investigation modal functionality
    showInvestigation(agentType, messageContent, messageId) {
        // Implementation for investigation modal
        console.log('[EnhancedLiveConversation] Investigation requested:', { agentType, messageContent, messageId });
    }
    
    refreshConversation() {
        console.log('[EnhancedLiveConversation] Refreshing conversation...');
        this.loadInitialConversation();
    }
    
    updateAPIStatus() {
        // This will be updated from the status endpoint
        console.log('[EnhancedLiveConversation] API status will be updated from status endpoint');
    }
    
    destroy() {
        // Clean up timers and socket connections
        Object.values(this.timers).forEach(timer => {
            if (timer) clearInterval(timer);
        });
        
        if (this.socket) {
            this.socket.disconnect();
        }
    }
}

// Initialize enhanced system when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('[Main] DOM loaded, initializing enhanced systems...');
    
    // Check if we're on a page that needs the enhanced conversation system
    const conversationContainer = document.getElementById('publicLiveStream');
    if (conversationContainer) {
        console.log('[Main] Enhanced conversation container detected, initializing live conversation...');
        window.enhancedConversationManager = new EnhancedLiveConversationManager();
    }
    
    console.log('[Main] All enhanced systems initialized successfully');
});

// Function to start conversation manually (global access)
function startConversation() {
    if (window.enhancedConversationManager) {
        window.enhancedConversationManager.startConversationManually();
    } else {
        console.error('Enhanced conversation manager not initialized');
    }
}

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { EnhancedLiveConversationManager };
}