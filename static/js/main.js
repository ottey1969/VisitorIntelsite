// API-Integrated Live AI Conversation Feed with Real Backend
// Perfect Roofing Team - Real Business Data

class LiveConversationManager {
    constructor() {
        this.config = {
            BACKEND_URL: '',                // Use same origin (port 5000)
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
            const response = await this.makeAPICall('/api/live-conversation-feed');
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
            const response = await this.makeAPICall('/api/live-conversation-latest');
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
        
        // Show modal using Bootstrap
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    }
    
    createInvestigationModal() {
        const modalHTML = `
            <div class="modal fade" id="investigation-modal" tabindex="-1" aria-labelledby="investigation-modal-label" aria-hidden="true">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header bg-primary text-white">
                            <h5 class="modal-title" id="investigation-modal-label">
                                <i class="fas fa-search me-2"></i>AI Investigation Analysis
                            </h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <!-- Content will be populated dynamically -->
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-outline-secondary" id="print-investigation">
                                <i class="fas fa-print me-1"></i>Print
                            </button>
                            <button type="button" class="btn btn-outline-primary" id="download-investigation">
                                <i class="fas fa-download me-1"></i>Download PDF
                            </button>
                            <button type="button" class="btn btn-primary" id="share-investigation">
                                <i class="fas fa-share me-1"></i>Share
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        return document.getElementById('investigation-modal');
    }
    
    async makeAPICall(endpoint, method = 'GET', data = null) {
        const url = `${this.config.BACKEND_URL}${endpoint}`;
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            },
            timeout: this.config.API_TIMEOUT
        };
        
        if (data && method !== 'GET') {
            options.body = JSON.stringify(data);
        }
        
        for (let attempt = 1; attempt <= this.config.RETRY_ATTEMPTS; attempt++) {
            try {
                const response = await fetch(url, options);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const result = await response.json();
                return result;
                
            } catch (error) {
                console.warn(`[API] Attempt ${attempt} failed for ${endpoint}:`, error.message);
                
                if (attempt === this.config.RETRY_ATTEMPTS) {
                    throw error;
                }
                
                // Wait before retry (exponential backoff)
                await new Promise(resolve => setTimeout(resolve, attempt * 1000));
            }
        }
    }
    
    startPolling() {
        // Clear existing timers
        this.stopPolling();
        
        // Start message checking
        this.timers.messageCheck = setInterval(() => {
            this.checkForNewMessages();
        }, this.config.MESSAGE_CHECK_INTERVAL);
        
        // Start general polling
        this.timers.polling = setInterval(() => {
            this.updateAPIStatus();
        }, this.config.POLLING_INTERVAL);
        
        console.log('[LiveConversation] Polling started');
    }
    
    stopPolling() {
        if (this.timers.messageCheck) {
            clearInterval(this.timers.messageCheck);
            this.timers.messageCheck = null;
        }
        
        if (this.timers.polling) {
            clearInterval(this.timers.polling);
            this.timers.polling = null;
        }
        
        if (this.timers.countdown) {
            clearInterval(this.timers.countdown);
            this.timers.countdown = null;
        }
        
        console.log('[LiveConversation] Polling stopped');
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
                this.updateAPIStatusDisplay();
            }
        } catch (error) {
            console.error('[API Status] Error:', error);
            // Set all to offline on error
            this.state.apiStatus = {
                openai: false,
                anthropic: false,
                perplexity: false,
                gemini: false
            };
            this.updateAPIStatusDisplay();
        }
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
                const isOnline = this.state.apiStatus[service];
                element.className = `badge ${isOnline ? 'bg-success' : 'bg-danger'}`;
                element.innerHTML = `<i class="fas fa-circle"></i> ${service.toUpperCase()} ${isOnline ? 'Online' : 'Offline'}`;
            }
        });
    }
    
    startCountdown() {
        let seconds = 45;
        
        this.timers.countdown = setInterval(() => {
            seconds--;
            this.updateCountdownDisplay(seconds);
            
            if (seconds <= 0) {
                seconds = 45; // Reset
                this.checkForNewMessages();
            }
        }, 1000);
    }
    
    updateCountdownDisplay(seconds) {
        const countdownElement = document.querySelector('.countdown-timer, #countdown-timer');
        if (countdownElement) {
            countdownElement.textContent = seconds;
        }
        
        // Update progress bar if exists
        const progressBar = document.querySelector('.countdown-progress');
        if (progressBar) {
            const percentage = (seconds / 45) * 100;
            progressBar.style.width = `${percentage}%`;
        }
    }
    
    resetCountdown() {
        if (this.timers.countdown) {
            clearInterval(this.timers.countdown);
        }
        this.startCountdown();
    }
    
    updateTopicDisplay() {
        const topicElements = document.querySelectorAll('.current-topic, .conversation-topic');
        topicElements.forEach(element => {
            if (element && this.state.currentTopic) {
                element.textContent = this.state.currentTopic;
            }
        });
    }
    
    updateRoundInfo() {
        // Update round number
        const roundElements = document.querySelectorAll('.round-number');
        roundElements.forEach(element => {
            if (element) {
                element.textContent = this.state.roundInfo.roundNumber;
            }
        });
        
        // Update message count
        const countElements = document.querySelectorAll('.message-count');
        countElements.forEach(element => {
            if (element) {
                element.textContent = this.state.roundInfo.messageCount;
            }
        });
        
        // Update messages remaining
        const remainingElements = document.querySelectorAll('.messages-remaining');
        remainingElements.forEach(element => {
            if (element) {
                element.textContent = this.state.roundInfo.messagesRemaining;
            }
        });
    }
    
    updateMessageCount() {
        const countElement = document.querySelector('.total-messages');
        if (countElement) {
            countElement.textContent = this.state.messages.length;
        }
    }
    
    setLoadingState(isLoading) {
        this.state.isLoading = isLoading;
        
        const loadingElements = document.querySelectorAll('.loading-indicator');
        loadingElements.forEach(element => {
            element.style.display = isLoading ? 'block' : 'none';
        });
        
        const refreshBtn = document.querySelector('.refresh-btn');
        if (refreshBtn) {
            refreshBtn.disabled = isLoading;
            if (isLoading) {
                refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Loading...';
            } else {
                refreshBtn.innerHTML = '<i class="fas fa-sync-alt me-1"></i>Refresh';
            }
        }
    }
    
    showActivityPulse() {
        // Add visual indication of new activity
        const container = document.querySelector('.conversation-messages, .live-conversation-feed');
        if (container) {
            container.classList.add('new-activity');
            setTimeout(() => {
                container.classList.remove('new-activity');
            }, 3000);
        }
    }
    
    showError(message) {
        const errorContainer = document.querySelector('.error-container');
        if (errorContainer) {
            errorContainer.innerHTML = `
                <div class="alert alert-danger alert-dismissible fade show" role="alert">
                    <i class="fas fa-exclamation-triangle me-2"></i>${message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            `;
            
            // Auto-dismiss after 5 seconds
            setTimeout(() => {
                const alert = errorContainer.querySelector('.alert');
                if (alert) {
                    const bsAlert = new bootstrap.Alert(alert);
                    bsAlert.close();
                }
            }, 5000);
        }
    }
    
    async refreshConversation() {
        console.log('[LiveConversation] Manual refresh requested');
        await this.loadInitialConversation();
    }
    
    // Investigation modal actions
    downloadInvestigation() {
        if (!this.currentInvestigation) return;
        
        const data = this.currentInvestigation;
        const content = `
AI Investigation Report
=====================

Business: ${data.business}
Agent: ${data.agent_type}
Confidence: ${data.confidence}%
Generated: ${new Date(data.generated_at).toLocaleString()}

Analysis:
${data.analysis}

Recommendations:
${data.recommendations.map((rec, i) => `${i + 1}. ${rec}`).join('\n')}
        `;
        
        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `investigation-${Date.now()}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
    
    printInvestigation() {
        if (!this.currentInvestigation) return;
        
        const printWindow = window.open('', '_blank');
        const data = this.currentInvestigation;
        
        printWindow.document.write(`
            <html>
                <head>
                    <title>AI Investigation Report</title>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 20px; }
                        .header { border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 20px; }
                        .section { margin-bottom: 20px; }
                        .recommendations { list-style-type: decimal; }
                    </style>
                </head>
                <body>
                    <div class="header">
                        <h1>AI Investigation Report</h1>
                        <p><strong>Business:</strong> ${data.business}</p>
                        <p><strong>Agent:</strong> ${data.agent_type}</p>
                        <p><strong>Confidence:</strong> ${data.confidence}%</p>
                        <p><strong>Generated:</strong> ${new Date(data.generated_at).toLocaleString()}</p>
                    </div>
                    
                    <div class="section">
                        <h2>Analysis</h2>
                        <p>${data.analysis.replace(/\n/g, '<br>')}</p>
                    </div>
                    
                    <div class="section">
                        <h2>Recommendations</h2>
                        <ol class="recommendations">
                            ${data.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                        </ol>
                    </div>
                </body>
            </html>
        `);
        
        printWindow.document.close();
        printWindow.print();
    }
    
    shareInvestigation() {
        if (!this.currentInvestigation) return;
        
        const data = this.currentInvestigation;
        const shareText = `AI Investigation Report for ${data.business}\n\nAnalysis: ${data.analysis}\n\nGenerated by ${data.agent_type} AI Agent`;
        
        if (navigator.share) {
            navigator.share({
                title: 'AI Investigation Report',
                text: shareText,
                url: window.location.href
            });
        } else {
            // Fallback: copy to clipboard
            navigator.clipboard.writeText(shareText).then(() => {
                alert('Investigation report copied to clipboard!');
            });
        }
    }
    
    // Cleanup method
    destroy() {
        this.stopPolling();
        console.log('[LiveConversation] Manager destroyed');
    }
}

// Dashboard Controls Manager
class DashboardControlsManager {
    constructor() {
        this.businessId = this.extractBusinessId();
        this.apiBaseUrl = 'http://localhost:5000';
        this.init();
    }
    
    extractBusinessId() {
        const pathParts = window.location.pathname.split('/');
        const businessIndex = pathParts.indexOf('business');
        return businessIndex !== -1 && pathParts[businessIndex + 1] ? pathParts[businessIndex + 1] : '1';
    }
    
    init() {
        this.setupDashboardControls();
        this.loadContentStatus();
    }
    
    setupDashboardControls() {
        // Add event listeners for dashboard actions
        document.addEventListener('click', (e) => {
            if (e.target.closest('[data-action]')) {
                e.preventDefault();
                const button = e.target.closest('[data-action]');
                const action = button.dataset.action;
                const contentType = button.dataset.contentType;
                
                this.handleDashboardAction(action, contentType, button);
            }
        });
    }
    
    async handleDashboardAction(action, contentType, button) {
        const originalHTML = button.innerHTML;
        button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Processing...';
        button.disabled = true;
        
        try {
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
        } catch (error) {
            console.error('Dashboard action error:', error);
            this.showNotification('Action failed. Please try again.', 'danger');
        } finally {
            button.innerHTML = originalHTML;
            button.disabled = false;
        }
    }
    
    async generateContent(contentType) {
        const response = await fetch(`${this.apiBaseUrl}/api/business/${this.businessId}/generate-content`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ contentType: contentType })
        });
        
        if (response.ok) {
            this.showNotification(`${contentType} content generated successfully!`, 'success');
            this.loadContentStatus(); // Refresh status
        } else {
            throw new Error('Generation failed');
        }
    }
    
    async viewContent(contentType) {
        const response = await fetch(`${this.apiBaseUrl}/api/business/${this.businessId}/content/${contentType}`);
        
        if (response.ok) {
            const content = await response.json();
            this.showContentModal(contentType, content);
        } else {
            throw new Error('Failed to load content');
        }
    }
    
    async downloadContent(contentType) {
        const response = await fetch(`${this.apiBaseUrl}/api/business/${this.businessId}/content/${contentType}/download`);
        
        if (response.ok) {
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${contentType}-content.pdf`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            this.showNotification(`${contentType} content downloaded!`, 'success');
        } else {
            throw new Error('Download failed');
        }
    }
    
    async deleteContent(contentType) {
        if (!confirm(`Are you sure you want to delete ${contentType} content? This cannot be undone.`)) {
            return;
        }
        
        const response = await fetch(`${this.apiBaseUrl}/api/business/${this.businessId}/content/${contentType}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            this.showNotification(`${contentType} content deleted successfully!`, 'success');
            this.loadContentStatus(); // Refresh status
        } else {
            throw new Error('Deletion failed');
        }
    }
    
    async loadContentStatus() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/business/${this.businessId}/content-status`);
            if (response.ok) {
                const status = await response.json();
                this.updateButtonStates(status);
            }
        } catch (error) {
            console.error('Failed to load content status:', error);
        }
    }
    
    updateButtonStates(status) {
        Object.keys(status).forEach(contentType => {
            const hasContent = status[contentType];
            const container = document.querySelector(`[data-content-type="${contentType}"]`)?.parentElement;
            
            if (container) {
                if (hasContent) {
                    // Show view/download/delete buttons
                    container.innerHTML = `
                        <button class="btn btn-outline-primary btn-sm mb-2" data-action="view" data-content-type="${contentType}">
                            <i class="fas fa-eye me-1"></i>View
                        </button>
                        <button class="btn btn-outline-success btn-sm mb-2" data-action="download" data-content-type="${contentType}">
                            <i class="fas fa-download me-1"></i>Download
                        </button>
                        <button class="btn btn-outline-danger btn-sm" data-action="delete" data-content-type="${contentType}">
                            <i class="fas fa-trash me-1"></i>Delete
                        </button>
                    `;
                } else {
                    // Show generate button
                    container.innerHTML = `
                        <button class="btn btn-primary btn-sm" data-action="generate" data-content-type="${contentType}">
                            <i class="fas fa-plus me-1"></i>Generate ${contentType}
                        </button>
                    `;
                }
            }
        });
    }
    
    showContentModal(contentType, content) {
        // Create and show modal with content
        const modalHTML = `
            <div class="modal fade" id="content-modal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">${contentType} Content</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <pre>${JSON.stringify(content, null, 2)}</pre>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal
        const existingModal = document.getElementById('content-modal');
        if (existingModal) {
            existingModal.remove();
        }
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        const modal = new bootstrap.Modal(document.getElementById('content-modal'));
        modal.show();
    }
    
    showNotification(message, type = 'info') {
        const alertHTML = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        // Find or create notification container
        let container = document.querySelector('.notification-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'notification-container position-fixed top-0 end-0 p-3';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }
        
        container.insertAdjacentHTML('beforeend', alertHTML);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            const alerts = container.querySelectorAll('.alert');
            if (alerts.length > 0) {
                alerts[0].remove();
            }
        }, 5000);
    }
}

// Initialize based on page type
document.addEventListener('DOMContentLoaded', function() {
    console.log('[Main] DOM loaded, initializing systems...');
    
    // Initialize live conversation manager on all pages
    window.liveConversationManager = new LiveConversationManager();
    
    // Initialize dashboard controls if on dashboard page
    if (window.location.pathname.includes('/business/') || window.location.pathname.includes('dashboard')) {
        window.dashboardControlsManager = new DashboardControlsManager();
    }
    
    console.log('[Main] All systems initialized successfully');
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (window.liveConversationManager) {
        window.liveConversationManager.destroy();
    }
});