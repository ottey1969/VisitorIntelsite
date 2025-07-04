// Visitor Intel - AI Conversation Platform with Business-Specific Live Feed Integration
// Connects all pages to real business conversation history with investigation features

class VisitorIntelConversationSystem {
    constructor() {
        this.pageType = this.detectPageType();
        this.businessId = this.extractBusinessId();
        this.conversationData = [];
        this.currentTopic = '';
        this.isPolling = true;
        this.investigationModal = null;
        
        // Polling intervals
        this.pollInterval = 30000; // 30 seconds
        this.statusCheckInterval = 60000; // 1 minute
        
        // AI services status
        this.aiServicesStatus = {
            openai: false,
            anthropic: false,
            perplexity: false,
            gemini: false
        };
        
        this.init();
    }
    
    detectPageType() {
        const url = window.location.pathname;
        if (url === '/' || url.includes('home')) {
            return 'homepage';
        } else if (url.includes('/business/')) {
            return 'dashboard';
        } else if (url.includes('/public/conversation/')) {
            return 'public_conversation';
        }
        return 'other';
    }
    
    extractBusinessId() {
        // Extract business ID from URL for dashboard pages
        const urlMatch = window.location.pathname.match(/\/business\/(\d+)/);
        return urlMatch ? parseInt(urlMatch[1]) : null;
    }
    
    init() {
        console.log(`Initializing Visitor Intel system for ${this.pageType} page`);
        
        // Initialize based on page type
        if (this.pageType === 'homepage') {
            this.initHomepage();
        } else if (this.pageType === 'dashboard') {
            this.initDashboard();
        }
        
        // Start background services
        this.checkAPIStatus();
        this.startPolling();
        
        // Set up page-specific listeners
        this.setupEventListeners();
    }
    
    initHomepage() {
        // For homepage, show featured business conversation
        this.loadFeaturedConversation();
    }
    
    initDashboard() {
        // For dashboard, load business-specific conversation
        if (this.businessId) {
            this.loadBusinessConversation(this.businessId);
        }
    }
    
    async loadFeaturedConversation() {
        try {
            const response = await fetch('/api/live-conversation');
            const data = await response.json();
            
            if (data.success) {
                this.displayConversation(data);
            } else {
                this.displayError('No live conversation available');
            }
        } catch (error) {
            console.error('Error loading featured conversation:', error);
            this.displayError('Failed to load conversation data');
        }
    }
    
    async loadBusinessConversation(businessId) {
        try {
            const response = await fetch(`/api/live-conversation/${businessId}`);
            const data = await response.json();
            
            if (data.success) {
                this.displayConversation(data);
            } else {
                this.displayError('No conversation data available for this business');
            }
        } catch (error) {
            console.error('Error loading business conversation:', error);
            this.displayError('Failed to load conversation data');
        }
    }
    
    displayConversation(data) {
        const container = document.getElementById('live-conversation-messages') || 
                         document.getElementById('conversation-feed') ||
                         document.querySelector('.conversation-messages');
        
        if (!container) {
            console.warn('No conversation container found on page');
            return;
        }
        
        // Update topic if element exists
        const topicElement = document.getElementById('conversation-topic') ||
                            document.getElementById('current-topic');
        if (topicElement) {
            topicElement.textContent = data.topic || 'Business Discussion';
        }
        
        // Display messages
        this.displayMessages(container, data.messages || [], data.topic || '');
        
        // Update analytics if available
        this.updateAnalytics(data);
    }
    
    displayMessages(container, messages, topic) {
        if (!messages || messages.length === 0) {
            container.innerHTML = `
                <div class="text-center py-4">
                    <i class="fas fa-comments text-muted fa-3x mb-3"></i>
                    <p class="text-muted">No conversation messages available</p>
                </div>
            `;
            return;
        }
        
        let html = '';
        messages.forEach((message, index) => {
            const agentColors = {
                'Business AI Assistant': 'primary',
                'SEO AI Specialist': 'success', 
                'Customer Service AI': 'info',
                'Marketing AI Expert': 'warning'
            };
            
            const agentColor = agentColors[message.agent_type] || 'secondary';
            
            html += `
                <div class="message-item mb-3 fade-in" style="animation-delay: ${index * 0.1}s;">
                    <div class="d-flex align-items-start">
                        <div class="avatar bg-${agentColor} bg-opacity-10 rounded-circle p-2 me-3">
                            <i class="fas fa-robot text-${agentColor}"></i>
                        </div>
                        <div class="flex-grow-1">
                            <div class="d-flex justify-content-between align-items-center mb-1">
                                <div class="fw-bold text-${agentColor}">${message.agent_name}</div>
                                <div class="d-flex align-items-center gap-2">
                                    <small class="text-muted">${message.timestamp}</small>
                                    <button class="btn btn-outline-primary btn-sm" onclick="visitorIntel.investigateMessage(${message.id}, \`${message.message_content.replace(/`/g, '\\`')}\`, '${message.agent_type}', \`${topic}\`)">
                                        <i class="fas fa-search me-1"></i>Investigate
                                    </button>
                                </div>
                            </div>
                            <span class="badge bg-${agentColor} bg-opacity-10 text-${agentColor} small mb-2">${message.agent_type}</span>
                            <p class="mb-0">${message.message_content}</p>
                        </div>
                    </div>
                </div>
            `;
        });
        
        container.innerHTML = html;
        
        // Auto-scroll to bottom
        container.scrollTop = container.scrollHeight;
    }
    
    async investigateMessage(messageId, messageContent, agentType, topic) {
        try {
            this.showInvestigationModal('Generating investigation...', []);
            
            const response = await fetch('/api/investigation', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    messageId: messageId,
                    messageContent: messageContent,
                    agentType: agentType,
                    topic: topic
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.updateInvestigationModal(data);
            } else {
                this.updateInvestigationModal({
                    title: 'Investigation Failed',
                    sections: [{ title: 'Error', content: data.error || 'Unable to generate investigation' }],
                    confidence: 0
                });
            }
        } catch (error) {
            console.error('Investigation error:', error);
            this.updateInvestigationModal({
                title: 'Investigation Error',
                sections: [{ title: 'Error', content: 'Failed to connect to investigation service' }],
                confidence: 0
            });
        }
    }
    
    showInvestigationModal(title, sections) {
        // Remove existing modal
        const existingModal = document.getElementById('investigationModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        const modalHtml = `
            <div class="modal fade" id="investigationModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="fas fa-search me-2"></i>Message Investigation
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body" id="investigation-content">
                            <div class="text-center py-4">
                                <div class="spinner-border text-primary" role="status"></div>
                                <p class="mt-2">${title}</p>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                            <button type="button" class="btn btn-primary" onclick="visitorIntel.downloadInvestigation()">
                                <i class="fas fa-download me-1"></i>Download Report
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        this.investigationModal = new bootstrap.Modal(document.getElementById('investigationModal'));
        this.investigationModal.show();
    }
    
    updateInvestigationModal(data) {
        const content = document.getElementById('investigation-content');
        if (!content) return;
        
        let html = `
            <div class="investigation-report">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h5>${data.title}</h5>
                    <span class="badge bg-success">${data.confidence}% Confidence</span>
                </div>
        `;
        
        if (data.sections && data.sections.length > 0) {
            data.sections.forEach(section => {
                html += `
                    <div class="investigation-section mb-3">
                        <h6 class="text-primary">${section.title}</h6>
                        <p>${section.content}</p>
                    </div>
                `;
            });
        }
        
        html += '</div>';
        content.innerHTML = html;
    }
    
    downloadInvestigation() {
        const content = document.getElementById('investigation-content');
        if (!content) return;
        
        const report = content.innerText;
        const blob = new Blob([report], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `visitor-intel-investigation-${Date.now()}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
    
    async checkAPIStatus() {
        try {
            const response = await fetch('/api-status');
            const data = await response.json();
            
            this.aiServicesStatus = {
                openai: data.openai || false,
                anthropic: data.anthropic || false,
                perplexity: data.perplexity || false,
                gemini: data.gemini || false
            };
            
            this.updateStatusIndicators();
        } catch (error) {
            console.error('Error checking API status:', error);
        }
    }
    
    updateStatusIndicators() {
        // Update status indicators if they exist on page
        const statusContainer = document.getElementById('api-status-indicators');
        if (statusContainer) {
            const services = Object.entries(this.aiServicesStatus);
            const allActive = services.every(([_, status]) => status);
            
            statusContainer.innerHTML = `
                <span class="badge bg-${allActive ? 'success' : 'warning'}">
                    <i class="fas fa-circle me-1"></i>
                    ${allActive ? 'All AI Services Active' : 'Partial Service'}
                </span>
            `;
        }
    }
    
    updateAnalytics(data) {
        // Update various analytics elements if they exist
        const elements = {
            'total-messages': data.messageCount,
            'current-business': data.business?.name,
            'conversation-count': 1
        };
        
        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element && value !== undefined) {
                element.textContent = value;
            }
        });
    }
    
    displayError(message) {
        const container = document.getElementById('live-conversation-messages') || 
                         document.getElementById('conversation-feed') ||
                         document.querySelector('.conversation-messages');
        
        if (container) {
            container.innerHTML = `
                <div class="alert alert-warning text-center">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    ${message}
                </div>
            `;
        }
    }
    
    refreshConversation() {
        console.log('Refreshing conversation data...');
        
        if (this.pageType === 'homepage') {
            this.loadFeaturedConversation();
        } else if (this.pageType === 'dashboard' && this.businessId) {
            this.loadBusinessConversation(this.businessId);
        }
        
        // Update status indicator if exists
        const statusIndicator = document.getElementById('status-indicator');
        if (statusIndicator) {
            statusIndicator.innerHTML = '<i class="fas fa-sync fa-spin me-1"></i>REFRESHING';
            statusIndicator.className = 'badge bg-warning';
            
            setTimeout(() => {
                statusIndicator.innerHTML = '<i class="fas fa-circle me-1"></i>LIVE';
                statusIndicator.className = 'badge bg-success';
            }, 2000);
        }
    }
    
    startPolling() {
        if (!this.isPolling) return;
        
        // Poll for conversation updates
        setInterval(() => {
            if (this.pageType === 'homepage') {
                this.loadFeaturedConversation();
            } else if (this.pageType === 'dashboard' && this.businessId) {
                this.loadBusinessConversation(this.businessId);
            }
        }, this.pollInterval);
        
        // Poll for API status updates
        setInterval(() => {
            this.checkAPIStatus();
        }, this.statusCheckInterval);
    }
    
    setupEventListeners() {
        // Global refresh button
        document.addEventListener('click', (e) => {
            if (e.target.matches('[onclick*="refreshConversation"]') || 
                e.target.closest('[onclick*="refreshConversation"]')) {
                e.preventDefault();
                this.refreshConversation();
            }
        });
        
        // Page visibility change handling
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible') {
                this.refreshConversation();
            }
        });
    }
}

// Initialize the system
let visitorIntel;

document.addEventListener('DOMContentLoaded', function() {
    visitorIntel = new VisitorIntelConversationSystem();
    
    // Add CSS animations
    if (!document.getElementById('visitor-intel-styles')) {
        const style = document.createElement('style');
        style.id = 'visitor-intel-styles';
        style.textContent = `
            .fade-in {
                animation: fadeIn 0.5s ease-in forwards;
                opacity: 0;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            .conversation-messages {
                scroll-behavior: smooth;
            }
            
            .message-item:hover {
                background-color: rgba(0,0,0,0.02);
                border-radius: 8px;
                padding: 8px;
                margin: -8px;
                transition: all 0.2s ease;
            }
            
            .investigation-report {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            
            .investigation-section {
                padding: 12px;
                background-color: rgba(0,123,255,0.05);
                border-left: 3px solid #007bff;
                border-radius: 4px;
            }
        `;
        document.head.appendChild(style);
    }
    
    console.log('Visitor Intel conversation system initialized successfully');
});

// Global functions for backward compatibility
function refreshConversation() {
    if (visitorIntel) {
        visitorIntel.refreshConversation();
    }
}

function investigateMessage(messageId, messageContent, agentType, topic) {
    if (visitorIntel) {
        visitorIntel.investigateMessage(messageId, messageContent, agentType, topic);
    }
}

// Auto-refresh prevention message
console.log('Auto-refresh disabled to maintain real-time timestamps');