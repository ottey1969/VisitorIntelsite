/**
 * Visitor Intel Frontend Fix - Complete Solution
 * =============================================
 * 
 * This module provides a complete frontend solution with:
 * - Dynamic status display (ACTIVE/WAITING with badges)
 * - Intelligent countdown timer
 * - UTC time display for all messages
 * - Real-time message handling via WebSockets
 * - Synchronized state management
 */

class VisitorIntelFrontend {
    constructor() {
        this.socket = null;
        this.currentState = {
            status: 'WAITING',
            conversation_active: false,
            messages_generated: 0,
            total_messages: 16,
            current_conversation_id: null,
            next_conversation_time: null,
            seconds_until_next: 0
        };
        
        this.countdownInterval = null;
        this.statusElements = {
            badge: document.getElementById('status-badge'),
            text: document.getElementById('status-text'),
            countdown: document.getElementById('countdown-display'),
            nextEvent: document.getElementById('next-event-text'),
            progressBar: document.getElementById('progress-bar'),
            messageCount: document.getElementById('message-count')
        };
        
        this.messageContainer = document.getElementById('message-container');
        this.conversationData = {
            id: null,
            topic: '',
            messages: []
        };
        
        this.init();
    }
    
    init() {
        this.connectWebSocket();
        this.loadInitialState();
        this.startCountdownTimer();
        this.setupEventListeners();
        console.log('[VisitorIntel] Frontend initialized');
    }
    
    connectWebSocket() {
        try {
            this.socket = io();
            
            this.socket.on('connect', () => {
                console.log('[VisitorIntel] Connected to server');
                this.loadInitialState();
            });
            
            this.socket.on('disconnect', () => {
                console.log('[VisitorIntel] Disconnected from server');
            });
            
            this.socket.on('system_state_update', (data) => {
                this.handleStateUpdate(data);
            });
            
            this.socket.on('new_message', (messageData) => {
                this.handleNewMessage(messageData);
            });
            
        } catch (error) {
            console.error('[VisitorIntel] WebSocket connection failed:', error);
            // Fallback to polling if WebSocket fails
            this.fallbackToPolling();
        }
    }
    
    loadInitialState() {
        fetch('/api/v2/status')
            .then(response => response.json())
            .then(data => {
                this.handleStateUpdate(data);
            })
            .catch(error => {
                console.error('[VisitorIntel] Failed to load initial state:', error);
                // Fallback to existing API
                this.loadFallbackState();
            });
    }
    
    loadFallbackState() {
        // Use existing API as fallback
        Promise.all([
            fetch('/api/system-status').then(r => r.json()),
            fetch('/api/live-conversation-latest').then(r => r.json())
        ])
        .then(([systemStatus, conversationData]) => {
            this.handleFallbackData(systemStatus, conversationData);
        })
        .catch(error => {
            console.error('[VisitorIntel] Fallback loading failed:', error);
        });
    }
    
    handleStateUpdate(data) {
        this.currentState = { ...this.currentState, ...data };
        this.updateUI();
        console.log('[VisitorIntel] State updated:', data.status);
    }
    
    handleNewMessage(messageData) {
        this.addMessageToUI(messageData);
        this.currentState.messages_generated = messageData.messageNumber;
        this.updateMessageCount();
        console.log('[VisitorIntel] New message received:', messageData.messageNumber);
    }
    
    updateUI() {
        this.updateStatusDisplay();
        this.updateCountdownDisplay();
        this.updateProgressDisplay();
        this.updateMessageCount();
    }
    
    updateStatusDisplay() {
        const { status, conversation_active } = this.currentState;
        
        if (this.statusElements.badge) {
            this.statusElements.badge.className = 'badge badge-' + 
                (conversation_active ? 'success' : 'secondary');
            this.statusElements.badge.textContent = status;
            
            // Add pulse animation for active state
            if (conversation_active) {
                this.statusElements.badge.classList.add('badge-pulse');
            } else {
                this.statusElements.badge.classList.remove('badge-pulse');
            }
        }
        
        if (this.statusElements.text) {
            this.statusElements.text.textContent = conversation_active 
                ? '4 AI Agents Are Having Live Discussion'
                : 'Waiting for Next AI Discussion';
        }
    }
    
    updateCountdownDisplay() {
        const { status, seconds_until_next, next_conversation_time } = this.currentState;
        
        if (!this.statusElements.countdown) return;
        
        if (status === 'ACTIVE') {
            // Show conversation progress
            const elapsed = this.currentState.elapsed_seconds || 0;
            const totalTime = 16 * 60; // 16 minutes
            const remaining = Math.max(0, totalTime - elapsed);
            
            this.statusElements.countdown.textContent = this.formatTimeRemaining(remaining);
            
            if (this.statusElements.nextEvent) {
                this.statusElements.nextEvent.textContent = 'Conversation in progress...';
            }
        } else {
            // Show countdown to next conversation
            if (seconds_until_next > 0) {
                this.statusElements.countdown.textContent = this.formatTimeRemaining(seconds_until_next);
                
                if (this.statusElements.nextEvent && next_conversation_time) {
                    const nextTime = new Date(next_conversation_time);
                    this.statusElements.nextEvent.textContent = 
                        `Next conversation at ${this.formatUTCTime(nextTime)}`;
                }
            } else {
                this.statusElements.countdown.textContent = 'Starting soon...';
                if (this.statusElements.nextEvent) {
                    this.statusElements.nextEvent.textContent = 'Preparing next conversation...';
                }
            }
        }
    }
    
    updateProgressDisplay() {
        if (!this.statusElements.progressBar) return;
        
        const { messages_generated, total_messages, status } = this.currentState;
        
        if (status === 'ACTIVE') {
            const percentage = Math.min(100, (messages_generated / total_messages) * 100);
            this.statusElements.progressBar.style.width = percentage + '%';
            this.statusElements.progressBar.style.display = 'block';
        } else {
            this.statusElements.progressBar.style.display = 'none';
        }
    }
    
    updateMessageCount() {
        if (this.statusElements.messageCount) {
            const { messages_generated, total_messages } = this.currentState;
            this.statusElements.messageCount.textContent = 
                `${messages_generated}/${total_messages} messages`;
        }
    }
    
    addMessageToUI(messageData) {
        if (!this.messageContainer) return;
        
        const messageElement = this.createMessageElement(messageData);
        
        // Add to top of container (newest first)
        if (this.messageContainer.firstChild) {
            this.messageContainer.insertBefore(messageElement, this.messageContainer.firstChild);
        } else {
            this.messageContainer.appendChild(messageElement);
        }
        
        // Animate in
        setTimeout(() => {
            messageElement.classList.add('message-fade-in');
        }, 10);
    }
    
    createMessageElement(messageData) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message-item mb-3 p-3 border rounded';
        messageDiv.setAttribute('data-message-id', messageData.id);
        
        const agentColor = this.getAgentColor(messageData.agent_type);
        const timestamp = this.formatUTCTime(new Date(messageData.timestamp));
        
        messageDiv.innerHTML = `
            <div class="d-flex justify-content-between align-items-start mb-2">
                <span class="badge badge-${agentColor}">${messageData.agent_name}</span>
                <small class="text-muted">${timestamp} UTC</small>
            </div>
            <p class="mb-0">${this.escapeHtml(messageData.content)}</p>
            <small class="text-muted">Round ${messageData.round}, Message ${messageData.messageNumber}</small>
        `;
        
        return messageDiv;
    }
    
    getAgentColor(agentType) {
        const colors = {
            'openai': 'primary',
            'anthropic': 'success',
            'perplexity': 'info',
            'gemini': 'warning'
        };
        return colors[agentType] || 'secondary';
    }
    
    formatUTCTime(date) {
        try {
            return date.toLocaleTimeString('en-US', {
                hour: 'numeric',
                minute: '2-digit',
                hour12: true,
                timeZone: 'UTC'
            });
        } catch (error) {
            console.error('[VisitorIntel] Error formatting time:', error);
            return 'Invalid Time';
        }
    }
    
    formatTimeRemaining(seconds) {
        if (seconds <= 0) return '00:00';
        
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        
        return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    startCountdownTimer() {
        // Clear existing interval
        if (this.countdownInterval) {
            clearInterval(this.countdownInterval);
        }
        
        // Update countdown every second
        this.countdownInterval = setInterval(() => {
            if (this.currentState.seconds_until_next > 0) {
                this.currentState.seconds_until_next--;
                this.updateCountdownDisplay();
            }
        }, 1000);
    }
    
    setupEventListeners() {
        // Handle page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                // Page became visible, refresh state
                this.loadInitialState();
            }
        });
        
        // Handle connection errors
        window.addEventListener('online', () => {
            console.log('[VisitorIntel] Connection restored');
            this.loadInitialState();
        });
        
        window.addEventListener('offline', () => {
            console.log('[VisitorIntel] Connection lost');
        });
    }
    
    fallbackToPolling() {
        console.log('[VisitorIntel] Falling back to polling mode');
        
        setInterval(() => {
            this.loadInitialState();
        }, 5000); // Poll every 5 seconds
    }
    
    handleFallbackData(systemStatus, conversationData) {
        // Convert existing API data to new format
        const state = {
            status: systemStatus.conversation_active ? 'ACTIVE' : 'WAITING',
            conversation_active: systemStatus.conversation_active,
            system_running: systemStatus.system_running,
            next_conversation_time: systemStatus.next_conversation_time,
            seconds_until_next: this.calculateSecondsUntil(systemStatus.next_conversation_time)
        };
        
        if (conversationData && conversationData.conversation_id) {
            state.current_conversation_id = conversationData.conversation_id;
            state.messages_generated = conversationData.messages ? conversationData.messages.length : 0;
            
            // Update messages if needed
            this.updateMessagesFromFallback(conversationData);
        }
        
        this.handleStateUpdate(state);
    }
    
    calculateSecondsUntil(timeString) {
        if (!timeString) return 0;
        
        try {
            const targetTime = new Date(timeString + (timeString.endsWith('Z') ? '' : 'Z'));
            const now = new Date();
            const diff = Math.max(0, Math.floor((targetTime - now) / 1000));
            return diff;
        } catch (error) {
            console.error('[VisitorIntel] Error calculating time difference:', error);
            return 0;
        }
    }
    
    updateMessagesFromFallback(conversationData) {
        // Only update if conversation changed or we don't have messages
        if (this.conversationData.id !== conversationData.conversation_id) {
            this.conversationData = conversationData;
            this.refreshMessageDisplay();
        }
    }
    
    refreshMessageDisplay() {
        if (!this.messageContainer || !this.conversationData.messages) return;
        
        // Clear existing messages
        this.messageContainer.innerHTML = '';
        
        // Add messages (newest first)
        const sortedMessages = [...this.conversationData.messages].reverse();
        sortedMessages.forEach(message => {
            this.addMessageToUI(message);
        });
    }
    
    destroy() {
        if (this.countdownInterval) {
            clearInterval(this.countdownInterval);
        }
        
        if (this.socket) {
            this.socket.disconnect();
        }
        
        console.log('[VisitorIntel] Frontend destroyed');
    }
}

// CSS for animations
const style = document.createElement('style');
style.textContent = `
    .badge-pulse {
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }
    
    .message-fade-in {
        animation: fadeIn 0.5s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .message-item {
        transition: all 0.3s ease;
    }
    
    .message-item:hover {
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
`;
document.head.appendChild(style);

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.visitorIntelFrontend = new VisitorIntelFrontend();
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (window.visitorIntelFrontend) {
        window.visitorIntelFrontend.destroy();
    }
});