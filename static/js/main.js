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
        this.startPolling();
        this.updateLocalTime();
        this.checkSystemStatus();
        
        // Initial load
        this.loadLatestConversation();
    }
    
    setupSocketIO() {
        if (typeof io !== 'undefined') {
            try {
                this.socket = io();
                this.socket.on('conversation_update', (data) => {
                    console.log('[SocketIO] Conversation update received:', data);
                    this.handleConversationUpdate(data);
                });
                this.socket.on('system_status', (data) => {
                    console.log('[SocketIO] System status update:', data);
                    this.updateSystemStatus(data);
                });
                console.log('[SocketIO] Connected successfully');
            } catch (error) {
                console.warn('[SocketIO] Connection failed, using polling fallback:', error);
            }
        }
    }
    
    setupEventListeners() {
        // Auto-refresh buttons
        const refreshButtons = document.querySelectorAll('.btn-refresh, .refresh-feed');
        refreshButtons.forEach(button => {
            button.addEventListener('click', () => this.loadLatestConversation());
        });
        
        // Generate conversation buttons
        const generateButtons = document.querySelectorAll('.btn-generate, .generate-conversation');
        generateButtons.forEach(button => {
            button.addEventListener('click', (e) => this.handleGenerateClick(e));
        });
        
        // Page visibility change
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pausePolling();
            } else {
                this.resumePolling();
            }
        });
    }
    
    startPolling() {
        this.stopPolling();
        
        // Main conversation polling
        this.timers.polling = setInterval(() => {
            this.loadLatestConversation();
        }, this.config.POLLING_INTERVAL);
        
        // Status check polling
        this.timers.statusCheck = setInterval(() => {
            this.checkSystemStatus();
            this.updateCountdown();
        }, this.config.STATUS_CHECK_INTERVAL);
        
        // Local time update
        this.timers.localTimeUpdate = setInterval(() => {
            this.updateLocalTime();
        }, 1000);
        
        console.log('[EnhancedPolling] Started with 5-second intervals');
    }
    
    stopPolling() {
        Object.values(this.timers).forEach(timer => {
            if (timer) clearInterval(timer);
        });
        Object.keys(this.timers).forEach(key => {
            this.timers[key] = null;
        });
    }
    
    pausePolling() {
        this.stopPolling();
        console.log('[EnhancedPolling] Paused due to page visibility');
    }
    
    resumePolling() {
        this.startPolling();
        this.loadLatestConversation();
        console.log('[EnhancedPolling] Resumed');
    }
    
    async apiRequest(endpoint, options = {}) {
        const url = `${this.config.BACKEND_URL}${endpoint}`;
        const defaultOptions = {
            timeout: this.config.API_TIMEOUT,
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        };
        
        const finalOptions = { ...defaultOptions, ...options };
        
        for (let attempt = 1; attempt <= this.config.RETRY_ATTEMPTS; attempt++) {
            try {
                console.log(`[API] Attempt ${attempt} for ${endpoint}`);
                
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), finalOptions.timeout);
                
                const response = await fetch(url, {
                    ...finalOptions,
                    signal: controller.signal
                });
                
                clearTimeout(timeoutId);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                console.log(`[API] Success for ${endpoint}:`, data);
                return { success: true, data };
                
            } catch (error) {
                console.warn(`[API] Attempt ${attempt} failed for ${endpoint}:`, error.message);
                
                if (attempt === this.config.RETRY_ATTEMPTS) {
                    console.error(`[API] All attempts failed for ${endpoint}`);
                    return { success: false, error: error.message };
                }
                
                // Exponential backoff
                await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt) * 1000));
            }
        }
    }
    
    async loadLatestConversation() {
        if (this.state.isLoading) return;
        
        this.state.isLoading = true;
        this.updateLoadingState(true);
        
        try {
            const result = await this.apiRequest('/api/live-conversation-latest');
            
            if (result.success && result.data) {
                this.handleConversationData(result.data);
            } else {
                this.handleAPIError(result.error || 'Unknown error');
            }
        } catch (error) {
            console.error('[API] Unexpected error:', error);
            this.handleAPIError(error.message);
        } finally {
            this.state.isLoading = false;
            this.updateLoadingState(false);
        }
    }
    
    async checkSystemStatus() {
        try {
            const result = await this.apiRequest('/api/system-status');
            
            if (result.success && result.data) {
                this.updateSystemStatus(result.data);
            }
        } catch (error) {
            console.warn('[SystemStatus] Check failed:', error);
        }
    }
    
    handleConversationData(data) {
        const {
            business_name,
            conversation_id,
            messages = [],
            topic,
            next_conversation_time,
            conversation_active = false,
            round_number = 1,
            total_messages = 0
        } = data;
        
        // Update state
        this.state.messages = messages;
        this.state.currentTopic = topic;
        this.state.lastUpdate = new Date();
        this.state.conversationActive = conversation_active;
        this.state.nextConversationTime = next_conversation_time ? new Date(next_conversation_time) : null;
        this.state.roundInfo = {
            roundNumber: round_number,
            messageCount: total_messages,
            messagesRemaining: Math.max(0, 16 - (total_messages % 16))
        };
        
        // Update UI
        this.updateConversationDisplay();
        this.updateBusinessInfo(business_name, conversation_id);
        this.updateRoundInfo();
        this.updateCountdown();
        
        console.log(`[ConversationData] Updated: ${messages.length} messages, Topic: ${topic}`);
    }
    
    updateConversationDisplay() {
        const container = document.getElementById('conversation-messages');
        if (!container) return;
        
        if (this.state.messages.length === 0) {
            container.innerHTML = this.getEmptyStateHTML();
            return;
        }
        
        const messagesHTML = this.state.messages.map(msg => this.createMessageHTML(msg)).join('');
        container.innerHTML = messagesHTML;
        
        // Auto-scroll to latest message
        const latestMessage = container.querySelector('.message-item:last-child');
        if (latestMessage) {
            latestMessage.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }
    
    createMessageHTML(message) {
        const {
            agent_name,
            agent_type,
            content,
            timestamp,
            round,
            messageNumber
        } = message;
        
        const agentConfig = this.getAgentConfig(agent_name, agent_type);
        const formattedTime = this.formatTimestamp(timestamp);
        const isEven = messageNumber % 2 === 0;
        
        return `
            <div class="message-item ${isEven ? 'message-even' : 'message-odd'} animate__animated animate__fadeInUp" 
                 data-round="${round}" data-message="${messageNumber}">
                <div class="message-header d-flex align-items-center justify-content-between">
                    <div class="d-flex align-items-center">
                        <div class="agent-avatar ${agentConfig.class}">
                            <i class="${agentConfig.icon}"></i>
                        </div>
                        <div class="ms-3">
                            <h6 class="mb-0 fw-bold">${agent_name}</h6>
                            <small class="text-muted">${agentConfig.description}</small>
                        </div>
                    </div>
                    <div class="message-meta text-end">
                        <small class="text-muted d-block">Round ${round} • Message ${messageNumber}</small>
                        <small class="text-muted">${formattedTime}</small>
                    </div>
                </div>
                <div class="message-content mt-3">
                    <p class="mb-0">${this.escapeHTML(content)}</p>
                </div>
            </div>
        `;
    }
    
    getAgentConfig(agentName, agentType) {
        const configs = {
            'Business AI Assistant': {
                icon: 'fas fa-briefcase',
                class: 'bg-primary',
                description: 'Business Strategy Expert'
            },
            'SEO AI Specialist': {
                icon: 'fas fa-search',
                class: 'bg-success',
                description: 'SEO & Marketing Expert'
            },
            'Customer Service AI': {
                icon: 'fas fa-headset',
                class: 'bg-info',
                description: 'Customer Experience Expert'
            },
            'Marketing AI Expert': {
                icon: 'fas fa-chart-line',
                class: 'bg-warning',
                description: 'Marketing & Analytics Expert'
            }
        };
        
        return configs[agentName] || {
            icon: 'fas fa-robot',
            class: 'bg-secondary',
            description: 'AI Assistant'
        };
    }
    
    formatTimestamp(timestamp) {
        if (!timestamp) return 'Just now';
        
        try {
            const date = new Date(timestamp);
            const now = new Date();
            const diffMs = now - date;
            const diffMins = Math.floor(diffMs / 60000);
            
            if (diffMins < 1) return 'Just now';
            if (diffMins < 60) return `${diffMins}m ago`;
            if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
            
            return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch (error) {
            return 'Recently';
        }
    }
    
    updateBusinessInfo(businessName, conversationId) {
        // Update business name displays
        const businessElements = document.querySelectorAll('.business-name, [data-business-name]');
        businessElements.forEach(element => {
            element.textContent = businessName || 'Perfect Roofing Team';
        });
        
        // Update conversation ID displays
        const conversationElements = document.querySelectorAll('.conversation-id, [data-conversation-id]');
        conversationElements.forEach(element => {
            element.textContent = `#${conversationId || 'N/A'}`;
        });
        
        // Update topic displays
        const topicElements = document.querySelectorAll('.current-topic, [data-current-topic]');
        topicElements.forEach(element => {
            element.textContent = this.state.currentTopic || 'Waiting for topic...';
        });
    }
    
    updateRoundInfo() {
        const { roundNumber, messageCount, messagesRemaining } = this.state.roundInfo;
        
        // Update round displays
        const roundElements = document.querySelectorAll('.current-round, [data-current-round]');
        roundElements.forEach(element => {
            element.textContent = `Round ${roundNumber}`;
        });
        
        // Update message count displays
        const countElements = document.querySelectorAll('.message-count, [data-message-count]');
        countElements.forEach(element => {
            element.textContent = `${messageCount} messages`;
        });
        
        // Update remaining messages
        const remainingElements = document.querySelectorAll('.messages-remaining, [data-messages-remaining]');
        remainingElements.forEach(element => {
            element.textContent = `${messagesRemaining} remaining`;
        });
        
        // Update progress bars
        const progressBars = document.querySelectorAll('.conversation-progress');
        progressBars.forEach(bar => {
            const percentage = ((16 - messagesRemaining) / 16) * 100;
            bar.style.width = `${percentage}%`;
            bar.setAttribute('aria-valuenow', percentage);
        });
    }
    
    updateCountdown() {
        if (!this.state.nextConversationTime) {
            this.updateCountdownDisplay('Generating conversations...');
            return;
        }
        
        const now = new Date();
        const nextTime = new Date(this.state.nextConversationTime);
        const diffMs = nextTime - now;
        
        if (diffMs <= 0) {
            this.updateCountdownDisplay('New conversation starting...');
            return;
        }
        
        const minutes = Math.floor(diffMs / 60000);
        const seconds = Math.floor((diffMs % 60000) / 1000);
        
        this.updateCountdownDisplay(`Next conversation in ${minutes}:${seconds.toString().padStart(2, '0')}`);
    }
    
    updateCountdownDisplay(text) {
        const countdownElements = document.querySelectorAll('.next-conversation-countdown, [data-countdown]');
        countdownElements.forEach(element => {
            element.textContent = text;
        });
    }
    
    updateLocalTime() {
        const now = new Date();
        const timeString = now.toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: true
        });
        
        const timeElements = document.querySelectorAll('.local-time, [data-local-time]');
        timeElements.forEach(element => {
            element.textContent = timeString;
        });
        
        this.state.localTime = now;
    }
    
    updateSystemStatus(status) {
        this.state.systemRunning = status.system_running || false;
        this.state.apiStatus = status.api_status || this.state.apiStatus;
        
        // Update API status indicators
        Object.entries(this.state.apiStatus).forEach(([api, isActive]) => {
            const indicators = document.querySelectorAll(`[data-api="${api}"]`);
            indicators.forEach(indicator => {
                indicator.className = indicator.className.replace(/bg-(success|danger)/, '');
                indicator.classList.add(isActive ? 'bg-success' : 'bg-danger');
                indicator.title = `${api.toUpperCase()}: ${isActive ? 'Active' : 'Inactive'}`;
            });
        });
        
        // Update system status indicator
        const systemIndicators = document.querySelectorAll('.system-status, [data-system-status]');
        systemIndicators.forEach(indicator => {
            indicator.className = indicator.className.replace(/text-(success|danger)/, '');
            indicator.classList.add(this.state.systemRunning ? 'text-success' : 'text-danger');
            indicator.textContent = this.state.systemRunning ? 'System Online' : 'System Offline';
        });
    }
    
    updateLoadingState(isLoading) {
        const loadingElements = document.querySelectorAll('.loading-indicator, [data-loading]');
        loadingElements.forEach(element => {
            element.style.display = isLoading ? 'block' : 'none';
        });
        
        const refreshButtons = document.querySelectorAll('.btn-refresh, .refresh-feed');
        refreshButtons.forEach(button => {
            button.disabled = isLoading;
            if (isLoading) {
                button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
            } else {
                button.innerHTML = '<i class="fas fa-sync"></i> Refresh';
            }
        });
    }
    
    handleAPIError(error) {
        console.error('[API] Error handling:', error);
        
        // Show error message in conversation area
        const container = document.getElementById('conversation-messages');
        if (container && this.state.messages.length === 0) {
            container.innerHTML = this.getErrorStateHTML(error);
        }
        
        // Update status indicators
        this.updateSystemStatus({
            system_running: false,
            api_status: {
                openai: false,
                anthropic: false,
                perplexity: false,
                gemini: false
            }
        });
    }
    
    async handleGenerateClick(event) {
        const button = event.target.closest('button');
        if (!button) return;
        
        button.disabled = true;
        const originalText = button.innerHTML;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
        
        try {
            const result = await this.apiRequest('/api/generate-conversation', {
                method: 'POST'
            });
            
            if (result.success) {
                // Immediately refresh to show new conversation
                setTimeout(() => this.loadLatestConversation(), 1000);
            } else {
                console.error('[Generate] Failed:', result.error);
            }
        } catch (error) {
            console.error('[Generate] Error:', error);
        } finally {
            setTimeout(() => {
                button.disabled = false;
                button.innerHTML = originalText;
            }, 3000);
        }
    }
    
    getEmptyStateHTML() {
        return `
            <div class="text-center py-5">
                <div class="mb-4">
                    <i class="fas fa-comments fa-3x text-muted"></i>
                </div>
                <h5 class="text-muted">No conversations yet</h5>
                <p class="text-muted">Waiting for AI agents to start their discussion...</p>
                <button class="btn btn-primary btn-refresh">
                    <i class="fas fa-sync"></i> Check for Updates
                </button>
            </div>
        `;
    }
    
    getErrorStateHTML(error) {
        return `
            <div class="text-center py-5">
                <div class="mb-4">
                    <i class="fas fa-exclamation-triangle fa-3x text-warning"></i>
                </div>
                <h5 class="text-warning">Connection Error</h5>
                <p class="text-muted">Unable to load conversations: ${this.escapeHTML(error)}</p>
                <button class="btn btn-warning btn-refresh">
                    <i class="fas fa-sync"></i> Retry
                </button>
            </div>
        `;
    }
    
    escapeHTML(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }
    
    handleConversationUpdate(data) {
        // Handle real-time updates from SocketIO
        console.log('[SocketIO] Processing conversation update:', data);
        this.handleConversationData(data);
    }
    
    destroy() {
        this.stopPolling();
        if (this.socket) {
            this.socket.disconnect();
        }
        console.log('[EnhancedLiveConversation] Destroyed');
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('[Enhanced] Initializing Live Conversation Manager...');
    window.liveConversationManager = new EnhancedLiveConversationManager();
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (window.liveConversationManager) {
        window.liveConversationManager.destroy();
    }
});