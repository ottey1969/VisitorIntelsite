// API-Integrated Live AI Conversation Feed with Real Backend
// Perfect Roofing Team - Real Business Data

class LiveConversationManager {
    constructor() {
        this.config = {
            BACKEND_URL: 'http://localhost:5000',
            POLLING_INTERVAL: 30000,        // 30 seconds
            MESSAGE_CHECK_INTERVAL: 45000,  // 45 seconds
            API_TIMEOUT: 10000,             // 10 seconds
            RETRY_ATTEMPTS: 3,              // 3 retry attempts
            MAX_MESSAGES: 20                // Keep last 20 messages
        };
        
        this.state = {
            messages: [],
            currentTopic: null,
            lastUpdate: null,
            isLoading: false,
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
            messageCheck: null,
            countdown: null
        };
        
        this.init();
    }
    
    init() {
        console.log('[LiveConversation] Initializing with real backend connection...');
        this.setupEventListeners();
        this.loadInitialConversation();
        this.startPolling();
        this.updateAPIStatus();
        this.startCountdown();
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
        
        // Investigation modal actions
        document.addEventListener('click', (e) => {
            if (e.target.id === 'download-investigation') {
                this.downloadInvestigation();
            } else if (e.target.id === 'print-investigation') {
                this.printInvestigation();
            } else if (e.target.id === 'share-investigation') {
                this.shareInvestigation();
            }
        });
        
        // Refresh button
        const refreshBtn = document.querySelector('.refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.refreshConversation();
            });
        }
    }
    
    async loadInitialConversation() {
        console.log('[LiveConversation] Loading initial conversation from backend...');
        this.setLoadingState(true);
        
        try {
            const response = await this.makeAPICall('/api/live-conversation');
            if (response.success) {
                this.state.messages = response.data.messages || [];
                this.state.currentTopic = response.data.topic;
                this.state.roundInfo = {
                    roundNumber: response.data.round_number || 1,
                    messageCount: response.data.message_count || 0,
                    messagesRemaining: 16 - (response.data.message_count || 0)
                };
                this.state.lastUpdate = new Date(response.data.last_update);
                
                this.renderMessages();
                this.updateTopicDisplay();
                this.updateRoundInfo();
                
                console.log('[LiveConversation] Initial conversation loaded successfully');
            } else {
                throw new Error('Failed to load conversation data');
            }
        } catch (error) {
            console.error('[LiveConversation] Error loading initial conversation:', error);
            this.showError('Unable to load live conversation. Please check your connection.');
        } finally {
            this.setLoadingState(false);
        }
    }
    
    async checkForNewMessages() {
        try {
            const response = await this.makeAPICall('/api/live-conversation/latest');
            if (response.success && response.new_message) {
                // New message available
                const newMessage = response.data;
                this.addNewMessage(newMessage);
                
                // Update round info
                if (response.round_info) {
                    this.state.roundInfo = response.round_info;
                    this.updateRoundInfo();
                }
                
                // Update topic if changed
                if (response.topic !== this.state.currentTopic) {
                    this.state.currentTopic = response.topic;
                    this.updateTopicDisplay();
                }
                
                console.log('[LiveConversation] New message received:', newMessage.agent_name);
            } else {
                // No new message, update countdown
                const nextMessageIn = response.next_message_in || 45;
                this.updateCountdownDisplay(nextMessageIn);
            }
        } catch (error) {
            console.error('[LiveConversation] Error checking for new messages:', error);
        }
    }
    
    addNewMessage(message) {
        // Add to beginning of array (newest first)
        this.state.messages.unshift(message);
        
        // Keep only last MAX_MESSAGES
        if (this.state.messages.length > this.config.MAX_MESSAGES) {
            this.state.messages = this.state.messages.slice(0, this.config.MAX_MESSAGES);
        }
        
        // Update last update time
        this.state.lastUpdate = new Date();
        
        // Re-render messages
        this.renderMessages();
        
        // Show activity pulse
        this.showActivityPulse();
        
        // Reset countdown
        this.resetCountdown();
    }
    
    renderMessages() {
        const container = document.querySelector('.conversation-messages, .live-conversation-feed, #conversation-container');
        if (!container) {
            console.warn('[LiveConversation] No conversation container found');
            return;
        }
        
        if (this.state.messages.length === 0) {
            container.innerHTML = `
                <div class="alert alert-info">
                    <i class="fas fa-info-circle me-2"></i>
                    Loading live conversation data...
                </div>
            `;
            return;
        }
        
        const messagesHTML = this.state.messages.map(message => this.renderMessage(message)).join('');
        container.innerHTML = messagesHTML;
        
        // Update message count display
        this.updateMessageCount();
    }
    
    renderMessage(message) {
        const agentColors = {
            'GPT': 'primary',
            'CLD': 'success', 
            'PPL': 'info',
            'GMI': 'warning'
        };
        
        const agentColor = agentColors[message.agent_name] || 'secondary';
        
        return `
            <div class="message-card card mb-3 border-0 shadow-sm" data-message-id="${message.id}">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <div class="d-flex align-items-center">
                            <span class="badge bg-${agentColor} me-2">${message.agent_name}</span>
                            <small class="text-muted">${message.agent_type} • Live Discussion</small>
                        </div>
                        <div class="d-flex align-items-center">
                            <small class="text-muted me-2">${message.timestamp}</small>
                            <div class="live-indicator">
                                <span class="badge bg-danger">
                                    <i class="fas fa-circle pulse-animation"></i> LIVE
                                </span>
                            </div>
                        </div>
                    </div>
                    
                    <p class="card-text mb-3">${message.message_content}</p>
                    
                    <div class="d-flex justify-content-between align-items-center">
                        <div class="source-info">
                            <i class="fas fa-link me-1"></i>
                            <small class="text-muted">Source Reference: 
                                <a href="${message.source_url}" target="_blank" class="text-decoration-none">
                                    ${message.source_url}
                                </a>
                                <span class="badge bg-secondary ms-1">Perfect Roofing Team</span>
                            </small>
                        </div>
                        <button class="btn btn-outline-primary btn-sm investigation-btn" 
                                data-message-id="${message.id}"
                                data-agent-type="${message.agent_type}"
                                data-message-content="${message.message_content}">
                            <i class="fas fa-search me-1"></i>Short Investigation
                        </button>
                    </div>
                </div>
            </div>
        `;
    }
    
    async showInvestigation(agentType, messageContent, messageId) {
        console.log('[Investigation] Requesting investigation for:', agentType);
        
        try {
            const response = await this.makeAPICall('/api/investigation', 'POST', {
                agentType: agentType,
                messageContent: messageContent,
                messageId: messageId
            });
            
            if (response.success) {
                this.displayInvestigationModal(response.data);
            } else {
                throw new Error('Investigation request failed');
            }
        } catch (error) {
            console.error('[Investigation] Error:', error);
            this.showError('Unable to generate investigation. Please try again.');
        }
    }
    
    displayInvestigationModal(data) {
        // Create modal if it doesn't exist
        let modal = document.getElementById('investigation-modal');
        if (!modal) {
            modal = this.createInvestigationModal();
        }
        
        // Populate modal content
        const modalTitle = modal.querySelector('.modal-title');
        const modalBody = modal.querySelector('.modal-body');
        
        modalTitle.textContent = data.title;
        
        modalBody.innerHTML = `
            <div class="investigation-content">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h6 class="mb-0">
                        <i class="fas fa-building me-2"></i>${data.business}
                    </h6>
                    <span class="badge bg-success">
                        <i class="fas fa-check-circle me-1"></i>${data.confidence}% Confidence
                    </span>
                </div>
                
                <div class="analysis-content mb-4">
                    <h6><i class="fas fa-chart-line me-2"></i>Analysis</h6>
                    <div class="analysis-text">${data.analysis.replace(/\n/g, '<br>')}</div>
                </div>
                
                <div class="recommendations-content">
                    <h6><i class="fas fa-lightbulb me-2"></i>Recommendations</h6>
                    <ul class="list-group list-group-flush">
                        ${data.recommendations.map(rec => `
                            <li class="list-group-item border-0 px-0">
                                <i class="fas fa-arrow-right text-primary me-2"></i>${rec}
                            </li>
                        `).join('')}
                    </ul>
                </div>
                
                <div class="investigation-meta mt-4 pt-3 border-top">
                    <small class="text-muted">
                        <i class="fas fa-clock me-1"></i>Generated: ${new Date(data.generated_at).toLocaleString()}
                        <span class="ms-3">
                            <i class="fas fa-robot me-1"></i>Agent: ${data.agent_type}
                        </span>
                    </small>
                </div>
            </div>
        `;
        
        // Store investigation data for download/share
        this.currentInvestigation = data;
        
        // Show modal
        const bootstrapModal = new bootstrap.Modal(modal);
        bootstrapModal.show();
    }
    
    createInvestigationModal() {
        const modalHTML = `
            <div class="modal fade" id="investigation-modal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Investigation Results</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <!-- Content will be populated by JavaScript -->
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-success" id="download-investigation">
                                <i class="fas fa-download me-1"></i>Download
                            </button>
                            <button type="button" class="btn btn-info" id="print-investigation">
                                <i class="fas fa-print me-1"></i>Print
                            </button>
                            <button type="button" class="btn btn-primary" id="share-investigation">
                                <i class="fas fa-share me-1"></i>Share
                            </button>
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        return document.getElementById('investigation-modal');
    }
    
    downloadInvestigation() {
        if (!this.currentInvestigation) return;
        
        const content = `# ${this.currentInvestigation.title}

**Business:** ${this.currentInvestigation.business}
**Confidence:** ${this.currentInvestigation.confidence}%
**Generated:** ${new Date(this.currentInvestigation.generated_at).toLocaleString()}
**Agent:** ${this.currentInvestigation.agent_type}

## Analysis
${this.currentInvestigation.analysis}

## Recommendations
${this.currentInvestigation.recommendations.map((rec, i) => `${i + 1}. ${rec}`).join('\n')}

---
Generated by Perfect Roofing Team AI Investigation System
`;
        
        const blob = new Blob([content], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `perfect_roofing_investigation_${Date.now()}.md`;
        a.click();
        URL.revokeObjectURL(url);
        
        this.showNotification('Investigation downloaded successfully', 'success');
    }
    
    printInvestigation() {
        if (!this.currentInvestigation) return;
        
        const printWindow = window.open('', '_blank');
        printWindow.document.write(`
            <html>
                <head>
                    <title>${this.currentInvestigation.title}</title>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 20px; }
                        .header { border-bottom: 2px solid #007bff; padding-bottom: 10px; margin-bottom: 20px; }
                        .meta { background: #f8f9fa; padding: 10px; border-radius: 5px; margin-bottom: 20px; }
                        .analysis { margin-bottom: 20px; }
                        .recommendations { margin-bottom: 20px; }
                        .recommendations ul { padding-left: 20px; }
                    </style>
                </head>
                <body>
                    <div class="header">
                        <h1>${this.currentInvestigation.title}</h1>
                    </div>
                    <div class="meta">
                        <strong>Business:</strong> ${this.currentInvestigation.business}<br>
                        <strong>Confidence:</strong> ${this.currentInvestigation.confidence}%<br>
                        <strong>Generated:</strong> ${new Date(this.currentInvestigation.generated_at).toLocaleString()}<br>
                        <strong>Agent:</strong> ${this.currentInvestigation.agent_type}
                    </div>
                    <div class="analysis">
                        <h2>Analysis</h2>
                        <p>${this.currentInvestigation.analysis.replace(/\n/g, '<br>')}</p>
                    </div>
                    <div class="recommendations">
                        <h2>Recommendations</h2>
                        <ul>
                            ${this.currentInvestigation.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                        </ul>
                    </div>
                </body>
            </html>
        `);
        printWindow.document.close();
        printWindow.print();
        
        this.showNotification('Investigation sent to printer', 'success');
    }
    
    shareInvestigation() {
        if (!this.currentInvestigation) return;
        
        const shareText = `${this.currentInvestigation.title}\n\nBusiness: ${this.currentInvestigation.business}\nConfidence: ${this.currentInvestigation.confidence}%\n\nGenerated by Perfect Roofing Team AI Investigation System`;
        
        if (navigator.share) {
            navigator.share({
                title: this.currentInvestigation.title,
                text: shareText,
                url: window.location.href
            });
        } else {
            // Fallback: copy to clipboard
            navigator.clipboard.writeText(shareText).then(() => {
                this.showNotification('Investigation copied to clipboard', 'success');
            });
        }
    }
    
    async updateAPIStatus() {
        try {
            const response = await this.makeAPICall('/api-status');
            if (response) {
                this.state.apiStatus = {
                    openai: response.openai || false,
                    anthropic: response.anthropic || false,
                    perplexity: response.perplexity || false,
                    gemini: response.gemini || false
                };
                this.renderAPIStatus();
            }
        } catch (error) {
            console.error('[LiveConversation] Error updating API status:', error);
        }
    }
    
    renderAPIStatus() {
        const statusContainer = document.querySelector('.api-status-container, .live-status-indicators');
        if (!statusContainer) return;
        
        const statusHTML = `
            <div class="api-status-grid">
                <div class="status-item ${this.state.apiStatus.gemini ? 'active' : 'inactive'}">
                    <i class="fab fa-google"></i>
                    <span>Google AI</span>
                    <small>${this.state.apiStatus.gemini ? 'Indexed' : 'Offline'}</small>
                </div>
                <div class="status-item ${this.state.apiStatus.openai ? 'active' : 'inactive'}">
                    <i class="fas fa-robot"></i>
                    <span>ChatGPT</span>
                    <small>${this.state.apiStatus.openai ? 'Crawled' : 'Offline'}</small>
                </div>
                <div class="status-item ${this.state.apiStatus.perplexity ? 'active' : 'inactive'}">
                    <i class="fas fa-search"></i>
                    <span>Perplexity</span>
                    <small>${this.state.apiStatus.perplexity ? 'Listed' : 'Offline'}</small>
                </div>
                <div class="status-item ${this.state.apiStatus.anthropic ? 'active' : 'inactive'}">
                    <i class="fas fa-brain"></i>
                    <span>Anthropic</span>
                    <small>${this.state.apiStatus.anthropic ? 'Ranked' : 'Offline'}</small>
                </div>
            </div>
        `;
        
        statusContainer.innerHTML = statusHTML;
    }
    
    startPolling() {
        // Clear existing timers
        this.clearTimers();
        
        // Start message checking
        this.timers.messageCheck = setInterval(() => {
            this.checkForNewMessages();
        }, this.config.MESSAGE_CHECK_INTERVAL);
        
        // Start API status updates
        this.timers.polling = setInterval(() => {
            this.updateAPIStatus();
        }, this.config.POLLING_INTERVAL);
        
        console.log('[LiveConversation] Polling started');
    }
    
    startCountdown() {
        this.resetCountdown();
    }
    
    resetCountdown() {
        if (this.timers.countdown) {
            clearInterval(this.timers.countdown);
        }
        
        let timeRemaining = 45; // 45 seconds until next message
        
        this.timers.countdown = setInterval(() => {
            timeRemaining--;
            this.updateCountdownDisplay(timeRemaining);
            
            if (timeRemaining <= 0) {
                this.resetCountdown();
            }
        }, 1000);
    }
    
    updateCountdownDisplay(seconds) {
        const countdownElements = document.querySelectorAll('.countdown-timer, .next-message-timer');
        const progressElements = document.querySelectorAll('.countdown-progress');
        
        countdownElements.forEach(el => {
            el.textContent = `Next AI conversation in ${seconds} seconds`;
        });
        
        progressElements.forEach(el => {
            const percentage = ((45 - seconds) / 45) * 100;
            el.style.width = `${percentage}%`;
        });
        
        // Show typing indicator when close to new message
        if (seconds <= 10) {
            this.showTypingIndicator();
        }
    }
    
    showTypingIndicator() {
        const typingContainer = document.querySelector('.typing-indicator-container');
        if (typingContainer) {
            const agents = ['GPT', 'CLD', 'PPL', 'GMI'];
            const randomAgent = agents[Math.floor(Math.random() * agents.length)];
            
            typingContainer.innerHTML = `
                <div class="typing-indicator">
                    <span class="badge bg-secondary me-2">${randomAgent}</span>
                    <span class="typing-text">AI Agent is typing</span>
                    <div class="typing-dots">
                        <span></span><span></span><span></span>
                    </div>
                </div>
            `;
            typingContainer.style.display = 'block';
            
            // Hide after 8 seconds
            setTimeout(() => {
                typingContainer.style.display = 'none';
            }, 8000);
        }
    }
    
    showActivityPulse() {
        const pulseElement = document.querySelector('.activity-pulse');
        if (pulseElement) {
            pulseElement.classList.add('active');
            setTimeout(() => {
                pulseElement.classList.remove('active');
            }, 2000);
        }
    }
    
    updateTopicDisplay() {
        const topicElements = document.querySelectorAll('.current-topic, .conversation-topic');
        topicElements.forEach(el => {
            el.textContent = this.state.currentTopic || 'Loading topic...';
        });
    }
    
    updateRoundInfo() {
        const roundElements = document.querySelectorAll('.round-info');
        roundElements.forEach(el => {
            el.innerHTML = `
                Round ${this.state.roundInfo.roundNumber} • 
                Message ${this.state.roundInfo.messageCount}/16 • 
                ${this.state.roundInfo.messagesRemaining} remaining
            `;
        });
    }
    
    updateMessageCount() {
        const countElements = document.querySelectorAll('.message-count');
        countElements.forEach(el => {
            el.textContent = this.state.messages.length;
        });
    }
    
    async refreshConversation() {
        console.log('[LiveConversation] Refreshing conversation...');
        await this.loadInitialConversation();
        this.showNotification('Conversation refreshed', 'success');
    }
    
    setLoadingState(isLoading) {
        this.state.isLoading = isLoading;
        const loadingElements = document.querySelectorAll('.loading-indicator');
        loadingElements.forEach(el => {
            el.style.display = isLoading ? 'block' : 'none';
        });
    }
    
    showError(message) {
        this.showNotification(message, 'error');
    }
    
    showNotification(message, type = 'info') {
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'info'} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        // Add to toast container or create one
        let toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
            document.body.appendChild(toastContainer);
        }
        
        toastContainer.appendChild(toast);
        
        // Show toast
        const bootstrapToast = new bootstrap.Toast(toast);
        bootstrapToast.show();
        
        // Remove after hiding
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }
    
    async makeAPICall(endpoint, method = 'GET', data = null) {
        const url = `${this.config.BACKEND_URL}${endpoint}`;
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            },
            signal: AbortSignal.timeout(this.config.API_TIMEOUT)
        };
        
        if (data && method !== 'GET') {
            options.body = JSON.stringify(data);
        }
        
        let lastError;
        
        for (let attempt = 1; attempt <= this.config.RETRY_ATTEMPTS; attempt++) {
            try {
                console.log(`[API] ${method} ${endpoint} (attempt ${attempt})`);
                const response = await fetch(url, options);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const result = await response.json();
                console.log(`[API] ${method} ${endpoint} - Success`);
                return result;
                
            } catch (error) {
                lastError = error;
                console.warn(`[API] ${method} ${endpoint} - Attempt ${attempt} failed:`, error.message);
                
                if (attempt < this.config.RETRY_ATTEMPTS) {
                    // Wait before retry (exponential backoff)
                    await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt) * 1000));
                }
            }
        }
        
        console.error(`[API] ${method} ${endpoint} - All attempts failed:`, lastError);
        throw lastError;
    }
    
    clearTimers() {
        Object.values(this.timers).forEach(timer => {
            if (timer) clearInterval(timer);
        });
        this.timers = { polling: null, messageCheck: null, countdown: null };
    }
    
    destroy() {
        console.log('[LiveConversation] Destroying manager...');
        this.clearTimers();
    }
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize on pages with conversation containers
    const conversationContainer = document.querySelector('.conversation-messages, .live-conversation-feed, #conversation-container');
    if (conversationContainer) {
        console.log('[LiveConversation] Initializing Live Conversation Manager...');
        window.liveConversationManager = new LiveConversationManager();
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.liveConversationManager) {
        window.liveConversationManager.destroy();
    }
});

// CSS for animations and styling
const style = document.createElement('style');
style.textContent = `
    .pulse-animation {
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    .typing-indicator {
        display: flex;
        align-items: center;
        padding: 10px;
        background: #f8f9fa;
        border-radius: 10px;
        margin: 10px 0;
    }
    
    .typing-dots {
        display: flex;
        margin-left: 10px;
    }
    
    .typing-dots span {
        width: 6px;
        height: 6px;
        background: #6c757d;
        border-radius: 50%;
        margin: 0 2px;
        animation: typing 1.4s infinite ease-in-out;
    }
    
    .typing-dots span:nth-child(1) { animation-delay: -0.32s; }
    .typing-dots span:nth-child(2) { animation-delay: -0.16s; }
    
    @keyframes typing {
        0%, 80%, 100% { transform: scale(0); }
        40% { transform: scale(1); }
    }
    
    .activity-pulse {
        position: fixed;
        top: 20px;
        right: 20px;
        width: 20px;
        height: 20px;
        background: #28a745;
        border-radius: 50%;
        opacity: 0;
        transition: opacity 0.3s;
        z-index: 1000;
    }
    
    .activity-pulse.active {
        opacity: 1;
        animation: pulse 1s infinite;
    }
    
    .api-status-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
        gap: 10px;
        margin: 10px 0;
    }
    
    .status-item {
        text-align: center;
        padding: 10px;
        border-radius: 8px;
        transition: all 0.3s;
    }
    
    .status-item.active {
        background: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }
    
    .status-item.inactive {
        background: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
    }
    
    .status-item i {
        display: block;
        font-size: 1.2em;
        margin-bottom: 5px;
    }
    
    .status-item span {
        display: block;
        font-weight: bold;
        font-size: 0.9em;
    }
    
    .status-item small {
        display: block;
        font-size: 0.8em;
        opacity: 0.8;
    }
    
    .countdown-progress {
        height: 4px;
        background: #007bff;
        transition: width 1s linear;
        border-radius: 2px;
    }
    
    .investigation-btn:hover {
        transform: translateY(-1px);
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .message-card {
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .message-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1) !important;
    }
    
    .analysis-text {
        white-space: pre-line;
        line-height: 1.6;
    }
`;
document.head.appendChild(style);

console.log('[LiveConversation] Script loaded successfully - Ready for real backend integration');

