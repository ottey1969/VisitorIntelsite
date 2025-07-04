// API-Integrated Live AI Conversation Feed with Real Backend
// Perfect Roofing Team - Real Business Data

class LiveConversationManager {
    constructor() {
        this.config = {
            BACKEND_URL: '',
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
            const response = await this.makeAPICall('/api/live-conversation-latest');
            if (response.status === 'success') {
                this.state.messages = response.messages || [];
                this.state.currentTopic = response.topic;
                this.state.roundInfo = {
                    roundNumber: response.round_number || 1,
                    messageCount: response.message_count || 0,
                    messagesRemaining: 16 - (response.message_count || 0)
                };
                this.state.lastUpdate = new Date(response.timestamp);
                
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
            const response = await this.makeAPICall('/api/live-conversation-latest');
            if (response.status === 'success' && response.messages && response.messages.length > this.state.messages.length) {
                // New messages available
                const newMessages = response.messages.slice(this.state.messages.length);
                newMessages.forEach(message => this.addNewMessage(message));
                
                // Update topic if changed
                if (response.topic !== this.state.currentTopic) {
                    this.state.currentTopic = response.topic;
                    this.updateTopicDisplay();
                }
                
                console.log('[LiveConversation] New messages received');
            }
        } catch (error) {
            console.error('[LiveConversation] Error checking for new messages:', error);
        }
    }
    
    addNewMessage(message) {
        // Add to end of array (chronological order)
        this.state.messages.push(message);
        
        // Keep only last MAX_MESSAGES
        if (this.state.messages.length > this.config.MAX_MESSAGES) {
            this.state.messages = this.state.messages.slice(-this.config.MAX_MESSAGES);
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
        const container = document.querySelector('.conversation-messages, .live-conversation-feed, #conversation-container, .live-conversation-stream');
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
        const timestamp = new Date(message.timestamp).toLocaleTimeString([], {hour: '2-digit', minute: '2-digit', second: '2-digit'});
        
        return `
            <div class="message-card card mb-3 border-0 shadow-sm" data-message-id="${message.id}">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <div class="d-flex align-items-center">
                            <span class="badge bg-${agentColor} me-2">${message.agent_name}</span>
                            <small class="text-muted">${message.agent_type} • Round ${message.round}</small>
                        </div>
                        <div class="d-flex align-items-center">
                            <small class="text-muted me-2">${timestamp}</small>
                            <div class="live-indicator">
                                <span class="badge bg-danger">
                                    <i class="fas fa-circle pulse-animation"></i> LIVE
                                </span>
                            </div>
                        </div>
                    </div>
                    
                    <p class="card-text mb-3 text-dark">${message.content}</p>
                    
                    <div class="d-flex justify-content-between align-items-center">
                        <div class="source-info">
                            <i class="fas fa-building me-1"></i>
                            <small class="text-muted">Perfect Roofing Team Discussion</small>
                        </div>
                        <button class="btn btn-outline-primary btn-sm investigation-btn" 
                                data-message-id="${message.id}"
                                data-agent-type="${message.agent_type}"
                                data-message-content="${encodeURIComponent(message.content)}"
                                onclick="console.log('Investigation clicked for:', '${message.agent_type}'); window.liveConversationManager.showInvestigation('${message.agent_type}', '${encodeURIComponent(message.content)}', '${message.id}');">
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
                agent_type: agentType,
                message_content: messageContent,
                message_id: messageId
            });
            
            if (response.success) {
                this.displayInvestigationModal(response);
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
        
        modalTitle.textContent = 'AI Investigation Analysis';
        
        modalBody.innerHTML = `
            <div class="investigation-content">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h6 class="mb-0">
                        <i class="fas fa-building me-2"></i>Perfect Roofing Team
                    </h6>
                    <span class="badge bg-success">
                        <i class="fas fa-check-circle me-1"></i>AI Analysis
                    </span>
                </div>
                
                <div class="analysis-content mb-4">
                    <h6><i class="fas fa-chart-line me-2"></i>Analysis Summary</h6>
                    <div class="analysis-text">${data.summary}</div>
                </div>
                
                <div class="recommendations-content">
                    <h6><i class="fas fa-lightbulb me-2"></i>Key Insights</h6>
                    <ul class="list-group list-group-flush">
                        ${data.key_insights.map(insight => `
                            <li class="list-group-item border-0 px-0">
                                <i class="fas fa-arrow-right text-primary me-2"></i>${insight}
                            </li>
                        `).join('')}
                    </ul>
                </div>
                
                <div class="investigation-meta mt-4 pt-3 border-top">
                    <small class="text-muted">
                        <i class="fas fa-clock me-1"></i>Generated: ${new Date(data.analysis_date).toLocaleString()}
                        <span class="ms-3">
                            <i class="fas fa-robot me-1"></i>Agent: ${data.agent_type.toUpperCase()}
                        </span>
                    </small>
                </div>
            </div>
        `;
        
        // Store investigation data for download/share
        this.currentInvestigation = data;
        
        // Show modal
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    }
    
    createInvestigationModal() {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'investigation-modal';
        modal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Investigation Analysis</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <!-- Content will be populated dynamically -->
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-outline-secondary" id="download-investigation">
                            <i class="fas fa-download me-1"></i>Download
                        </button>
                        <button type="button" class="btn btn-outline-primary" id="print-investigation">
                            <i class="fas fa-print me-1"></i>Print
                        </button>
                        <button type="button" class="btn btn-primary" id="share-investigation">
                            <i class="fas fa-share-alt me-1"></i>Share
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        return modal;
    }
    
    async makeAPICall(endpoint, method = 'GET', data = null) {
        const url = `${this.config.BACKEND_URL}${endpoint}`;
        
        for (let attempt = 1; attempt <= this.config.RETRY_ATTEMPTS; attempt++) {
            try {
                console.log(`[API] Attempt ${attempt} for ${endpoint}`);
                
                const options = {
                    method: method,
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    timeout: this.config.API_TIMEOUT
                };
                
                if (data && (method === 'POST' || method === 'PUT')) {
                    options.body = JSON.stringify(data);
                }
                
                const response = await fetch(url, options);
                const result = await response.json();
                
                console.log(`[API] Success for ${endpoint}:`, result);
                return result;
                
            } catch (error) {
                console.warn(`[API] Attempt ${attempt} failed for ${endpoint}:`, error.message);
                
                if (attempt === this.config.RETRY_ATTEMPTS) {
                    console.error(`[API] All attempts failed for ${endpoint}`);
                    throw error;
                }
                
                // Wait before retry
                await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
            }
        }
    }
    
    startPolling() {
        console.log('[LiveConversation] Starting polling for new messages...');
        
        // Clear existing timers
        this.stopPolling();
        
        // Start checking for new messages
        this.timers.messageCheck = setInterval(() => {
            this.checkForNewMessages();
        }, this.config.MESSAGE_CHECK_INTERVAL);
        
        console.log('[LiveConversation] Polling started');
    }
    
    stopPolling() {
        if (this.timers.messageCheck) {
            clearInterval(this.timers.messageCheck);
            this.timers.messageCheck = null;
        }
        console.log('[LiveConversation] Polling stopped');
    }
    
    async updateAPIStatus() {
        try {
            const response = await this.makeAPICall('/api-status');
            if (response.status === 'healthy') {
                this.state.apiStatus = response.services || {
                    openai: true,
                    anthropic: true,
                    perplexity: true,
                    gemini: true
                };
            } else {
                this.state.apiStatus = {
                    openai: false,
                    anthropic: false,
                    perplexity: false,
                    gemini: false
                };
            }
        } catch (error) {
            console.error('[API Status] Error:', error);
            this.state.apiStatus = {
                openai: false,
                anthropic: false,
                perplexity: false,
                gemini: false
            };
        }
        
        this.updateAPIStatusDisplay();
    }
    
    updateAPIStatusDisplay() {
        const statusElements = {
            'openai': document.querySelector('.api-status-openai'),
            'anthropic': document.querySelector('.api-status-anthropic'),
            'perplexity': document.querySelector('.api-status-perplexity'),
            'gemini': document.querySelector('.api-status-gemini')
        };
        
        Object.keys(statusElements).forEach(service => {
            const element = statusElements[service];
            if (element) {
                const isActive = this.state.apiStatus[service];
                element.className = isActive ? 'badge bg-success' : 'badge bg-danger';
                element.innerHTML = isActive ? 
                    `<i class="fas fa-check-circle me-1"></i>${service.toUpperCase()}` :
                    `<i class="fas fa-times-circle me-1"></i>${service.toUpperCase()}`;
            }
        });
    }
    
    startCountdown() {
        this.timers.countdown = setInterval(() => {
            // Update countdown every second
            this.updateCountdownDisplay();
        }, 1000);
    }
    
    updateCountdownDisplay(seconds = null) {
        const countdownElement = document.querySelector('.next-message-countdown');
        if (countdownElement) {
            const timeLeft = seconds || Math.max(0, 45 - Math.floor((Date.now() - (this.state.lastUpdate?.getTime() || Date.now())) / 1000));
            countdownElement.textContent = `Next message in: ${timeLeft}s`;
        }
    }
    
    resetCountdown() {
        this.state.lastUpdate = new Date();
    }
    
    updateTopicDisplay() {
        const topicElements = document.querySelectorAll('.current-topic, .conversation-topic');
        topicElements.forEach(element => {
            if (element) {
                element.textContent = this.state.currentTopic || 'Loading topic...';
            }
        });
    }
    
    updateRoundInfo() {
        const roundElement = document.querySelector('.round-info');
        if (roundElement) {
            roundElement.textContent = `Round ${this.state.roundInfo.roundNumber}`;
        }
    }
    
    updateMessageCount() {
        const countElement = document.querySelector('.message-count');
        if (countElement) {
            countElement.textContent = `${this.state.messages.length} messages`;
        }
    }
    
    setLoadingState(isLoading) {
        this.state.isLoading = isLoading;
        
        const loadingElements = document.querySelectorAll('.loading-indicator');
        loadingElements.forEach(element => {
            element.style.display = isLoading ? 'block' : 'none';
        });
    }
    
    showActivityPulse() {
        const pulseElements = document.querySelectorAll('.pulse-animation');
        pulseElements.forEach(element => {
            element.classList.add('pulse-active');
            setTimeout(() => {
                element.classList.remove('pulse-active');
            }, 2000);
        });
    }
    
    showError(message) {
        const errorContainer = document.querySelector('.error-container');
        if (errorContainer) {
            errorContainer.innerHTML = `
                <div class="alert alert-danger alert-dismissible fade show">
                    <i class="fas fa-exclamation-triangle me-2"></i>${message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            `;
        } else {
            console.error('[LiveConversation] Error:', message);
        }
    }
    
    async refreshConversation() {
        console.log('[LiveConversation] Manual refresh triggered');
        await this.loadInitialConversation();
        this.showNotification('Conversation refreshed', 'success');
    }
    
    showNotification(message, type = 'info') {
        // Create a simple notification
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 250px;';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 3000);
    }
    
    downloadInvestigation() {
        if (!this.currentInvestigation) return;
        
        const content = `
Investigation Analysis Report
===========================

Business: Perfect Roofing Team
Agent: ${this.currentInvestigation.agent_type.toUpperCase()}
Generated: ${new Date(this.currentInvestigation.analysis_date).toLocaleString()}

Analysis Summary:
${this.currentInvestigation.summary}

Key Insights:
${this.currentInvestigation.key_insights.map(insight => `• ${insight}`).join('\n')}

---
Generated by Visitor Intel AI Platform
        `;
        
        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `investigation-analysis-${Date.now()}.txt`;
        a.click();
        URL.revokeObjectURL(url);
    }
    
    printInvestigation() {
        if (!this.currentInvestigation) return;
        
        const printWindow = window.open('', '_blank');
        printWindow.document.write(`
            <html>
                <head>
                    <title>Investigation Analysis Report</title>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 20px; }
                        h1 { color: #333; }
                        .meta { color: #666; margin-bottom: 20px; }
                        .insights { margin-top: 20px; }
                        .insights ul { list-style-type: disc; margin-left: 20px; }
                    </style>
                </head>
                <body>
                    <h1>Investigation Analysis Report</h1>
                    <div class="meta">
                        <strong>Business:</strong> Perfect Roofing Team<br>
                        <strong>Agent:</strong> ${this.currentInvestigation.agent_type.toUpperCase()}<br>
                        <strong>Generated:</strong> ${new Date(this.currentInvestigation.analysis_date).toLocaleString()}
                    </div>
                    
                    <h2>Analysis Summary</h2>
                    <p>${this.currentInvestigation.summary}</p>
                    
                    <div class="insights">
                        <h2>Key Insights</h2>
                        <ul>
                            ${this.currentInvestigation.key_insights.map(insight => `<li>${insight}</li>`).join('')}
                        </ul>
                    </div>
                </body>
            </html>
        `);
        printWindow.document.close();
        printWindow.print();
    }
    
    shareInvestigation() {
        if (!this.currentInvestigation) return;
        
        const shareText = `Investigation Analysis - Perfect Roofing Team\n\n${this.currentInvestigation.summary}\n\nGenerated by Visitor Intel AI Platform`;
        
        if (navigator.share) {
            navigator.share({
                title: 'Investigation Analysis Report',
                text: shareText,
                url: window.location.href
            });
        } else {
            // Fallback: copy to clipboard
            navigator.clipboard.writeText(shareText).then(() => {
                this.showNotification('Investigation analysis copied to clipboard!', 'success');
            });
        }
    }
    
    destroy() {
        this.stopPolling();
        if (this.timers.countdown) {
            clearInterval(this.timers.countdown);
        }
    }
}

// Dashboard Controls Manager for business dashboards
class DashboardControlsManager {
    constructor() {
        this.businessId = this.extractBusinessId();
        this.init();
    }
    
    extractBusinessId() {
        const pathMatch = window.location.pathname.match(/\/business\/(\d+)/);
        return pathMatch ? pathMatch[1] : '1';
    }
    
    init() {
        this.setupDashboardControls();
        this.loadContentStatus();
    }
    
    setupDashboardControls() {
        document.addEventListener('click', (e) => {
            const target = e.target.closest('button');
            if (!target) return;
            
            const action = target.dataset.action;
            const contentType = target.dataset.contentType;
            
            if (action && contentType) {
                e.preventDefault();
                this.handleDashboardAction(action, contentType, target);
            }
        });
    }
    
    async handleDashboardAction(action, contentType, button) {
        switch (action) {
            case 'generate':
                await this.generateContent(contentType);
                break;
            case 'view':
                await this.viewContent(contentType);
                break;
            case 'download':
                await this.downloadContent(contentType);
                break;
            case 'delete':
                await this.deleteContent(contentType);
                break;
        }
    }
    
    async generateContent(contentType) {
        this.showNotification(`Generating ${contentType} content...`, 'info');
        // Implementation would call backend API
        setTimeout(() => {
            this.showNotification(`${contentType} content generated successfully!`, 'success');
        }, 2000);
    }
    
    async viewContent(contentType) {
        this.showContentModal(contentType, `Sample ${contentType} content for Perfect Roofing Team`);
    }
    
    async downloadContent(contentType) {
        this.showNotification(`Downloading ${contentType} content...`, 'info');
    }
    
    async deleteContent(contentType) {
        if (confirm(`Are you sure you want to delete the ${contentType} content?`)) {
            this.showNotification(`${contentType} content deleted`, 'warning');
        }
    }
    
    async loadContentStatus() {
        // Mock implementation - would call real API
        console.log('[Dashboard] Loading content status for business:', this.businessId);
    }
    
    updateButtonStates(status) {
        // Update button states based on content status
        Object.keys(status).forEach(contentType => {
            const container = document.querySelector(`[data-content-type="${contentType}"]`);
            if (container) {
                const buttonContainer = container.querySelector('.button-container');
                if (buttonContainer) {
                    // Update buttons based on status
                }
            }
        });
    }
    
    showContentModal(contentType, content) {
        // Create and show modal with content
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">${contentType} Content</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <pre>${content}</pre>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
        
        modal.addEventListener('hidden.bs.modal', () => {
            modal.remove();
        });
    }
    
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 250px;';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 3000);
    }
}

// Initialize based on page type
document.addEventListener('DOMContentLoaded', function() {
    console.log('[Main] DOM loaded, initializing systems...');
    
    // Check if we're on a business dashboard page
    if (window.location.pathname.includes('/business/')) {
        console.log('[Main] Business dashboard detected, initializing dashboard controls...');
        window.dashboardManager = new DashboardControlsManager();
    }
    
    // Always initialize live conversation manager if container exists
    if (document.querySelector('.conversation-messages, .live-conversation-feed, #conversation-container, .live-conversation-stream')) {
        console.log('[Main] Conversation container detected, initializing live conversation...');
        window.liveConversationManager = new LiveConversationManager();
    }
    
    console.log('[Main] All systems initialized successfully');
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (window.liveConversationManager) {
        window.liveConversationManager.destroy();
    }
});