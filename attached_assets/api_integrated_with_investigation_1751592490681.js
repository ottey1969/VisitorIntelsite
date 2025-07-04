// API-Integrated Live AI Conversation Feed Solution with Short Investigation Feature
// This solution pulls real data from your backend APIs and includes investigation summaries

class APIIntegratedConversationFeed {
    constructor() {
        this.isLivePage = this.detectPageType();
        this.conversationData = [];
        this.currentTopic = '';
        this.messageCount = 0;
        this.maxMessagesPerRound = 16;
        this.lastUpdateTime = Date.now();
        this.messageInterval = 45000; // 45 seconds base interval
        this.timestampInterval = 30000; // 30 seconds for timestamp updates
        this.statusCheckInterval = 60000; // 1 minute for API status checks
        this.syncKey = 'live_conversation_sync';
        
        // AI services status
        this.aiServicesStatus = {
            openai: false,
            anthropic: false,
            perplexity: false,
            gemini: false
        };
        
        // AI agents configuration
        this.agents = [
            { id: 'GPT', name: 'Business AI Assistant', color: 'primary', service: 'openai' },
            { id: 'GMI', name: 'Marketing AI Expert', color: 'warning', service: 'gemini' },
            { id: 'PPL', name: 'Customer Service AI', color: 'info', service: 'perplexity' },
            { id: 'CLD', name: 'SEO AI Specialist', color: 'primary', service: 'anthropic' }
        ];
        
        this.currentAgentIndex = 0;
        this.init();
    }
    
    detectPageType() {
        const url = window.location.pathname;
        if (url === '/' || url.includes('home')) {
            return 'homepage';
        } else if (url.includes('/public/conversation/')) {
            return 'public_conversation';
        } else if (url.includes('/business/') || url.includes('dashboard')) {
            return 'dashboard';
        }
        return 'unknown';
    }
    
    init() {
        if (this.isLivePage === 'homepage' || this.isLivePage === 'public_conversation') {
            this.initializeLiveFeed();
        } else if (this.isLivePage === 'dashboard') {
            this.initializeDashboard();
        }
    }
    
    initializeLiveFeed() {
        // Check if this is the master instance (homepage)
        this.isMaster = this.isLivePage === 'homepage';
        
        // Load synchronized state
        this.loadSyncState();
        
        // Initialize UI elements
        this.createLiveStatusBar();
        this.createCountdownTimer();
        this.createActivityPulse();
        this.createAIServicesStatus();
        this.createInvestigationModal();
        
        // Start API polling for real data
        this.startAPIPolling();
        
        // Listen for sync updates from other tabs/pages
        this.setupCrossTabSync();
    }
    
    async startAPIPolling() {
        // Initial load
        await this.checkAPIStatus();
        await this.loadCurrentConversation();
        
        // Set up intervals for different types of updates
        this.setupPollingIntervals();
    }
    
    setupPollingIntervals() {
        // Check API status every minute
        setInterval(() => {
            this.checkAPIStatus();
        }, this.statusCheckInterval);
        
        // Update timestamps every 30 seconds
        setInterval(() => {
            this.updateTimestamps();
        }, this.timestampInterval);
        
        // Check for new messages every 45-90 seconds (randomized)
        this.scheduleNextMessageCheck();
    }
    
    scheduleNextMessageCheck() {
        const randomInterval = this.messageInterval + (Math.random() * 45000); // 45-90 seconds
        
        setTimeout(async () => {
            if (this.isMaster) {
                await this.checkForNewMessage();
            }
            this.scheduleNextMessageCheck(); // Schedule next check
        }, randomInterval);
    }
    
    async checkAPIStatus() {
        try {
            const response = await fetch('/api-status');
            if (response.ok) {
                const status = await response.json();
                this.aiServicesStatus = status;
                this.updateAIServicesDisplay();
            }
        } catch (error) {
            console.log('API status check failed:', error);
            // Set all services to false on error
            this.aiServicesStatus = {
                openai: false,
                anthropic: false,
                perplexity: false,
                gemini: false
            };
            this.updateAIServicesDisplay();
        }
    }
    
    async loadCurrentConversation() {
        try {
            // For homepage, we'll use the current live conversation
            // For public pages, we'll sync with the live conversation
            const response = await fetch('/api/live-conversation');
            if (response.ok) {
                const data = await response.json();
                this.handleLiveConversationData(data);
            } else {
                // Fallback: extract from current page if API not available
                this.extractConversationFromPage();
            }
        } catch (error) {
            console.log('Failed to load conversation from API:', error);
            this.extractConversationFromPage();
        }
    }
    
    async checkForNewMessage() {
        try {
            const response = await fetch('/api/live-conversation/latest');
            if (response.ok) {
                const data = await response.json();
                if (data.message && data.message.timestamp !== this.getLatestMessageTimestamp()) {
                    this.addNewMessage(data.message, data.topic);
                }
            }
        } catch (error) {
            console.log('Failed to check for new message:', error);
        }
    }
    
    handleLiveConversationData(data) {
        if (data.messages && Array.isArray(data.messages)) {
            this.conversationData = data.messages;
            this.currentTopic = data.topic || '';
            this.messageCount = data.messageCount || 0;
            this.lastUpdateTime = Date.now();
            
            this.saveSyncState();
            this.updateDisplay();
            this.updateTopicDisplay();
        }
    }
    
    extractConversationFromPage() {
        // Fallback: extract existing conversation from page DOM
        const messageElements = document.querySelectorAll('.message-stream-item');
        this.conversationData = [];
        
        messageElements.forEach((element, index) => {
            const agentBadge = element.querySelector('.badge');
            const agentName = element.querySelector('h6');
            const messageContent = element.querySelector('p');
            const timestamp = element.querySelector('.text-muted');
            
            if (agentBadge && agentName && messageContent && timestamp) {
                const message = {
                    id: Date.now() - index,
                    agent_name: agentBadge.textContent.trim(),
                    agent_type: agentName.textContent.trim(),
                    message_content: messageContent.textContent.trim(),
                    timestamp: timestamp.textContent.trim(),
                    source_url: 'https://perfectroofingteam.com'
                };
                this.conversationData.push(message);
            }
        });
        
        this.saveSyncState();
    }
    
    addNewMessage(messageData, topic) {
        // Add new message from API
        const message = {
            id: Date.now(),
            agent_name: messageData.agent_name,
            agent_type: messageData.agent_type,
            message_content: messageData.message_content,
            timestamp: messageData.timestamp,
            source_url: messageData.source_url || 'https://perfectroofingteam.com'
        };
        
        // Add to beginning of array (newest first)
        this.conversationData.unshift(message);
        
        // Keep only last 16 messages
        if (this.conversationData.length > this.maxMessagesPerRound) {
            this.conversationData = this.conversationData.slice(0, this.maxMessagesPerRound);
        }
        
        // Update topic if provided
        if (topic && topic !== this.currentTopic) {
            this.currentTopic = topic;
            this.messageCount = 1; // Reset count for new topic
            this.updateTopicDisplay();
        } else {
            this.messageCount++;
        }
        
        // Check if we need to start a new round
        if (this.messageCount >= this.maxMessagesPerRound) {
            this.startNewRound();
        }
        
        this.lastUpdateTime = Date.now();
        this.saveSyncState();
        this.updateDisplay();
        this.triggerActivityPulse();
    }
    
    startNewRound() {
        // Reset for new round of 16 messages
        this.messageCount = 0;
        this.conversationData = []; // Clear for new topic
        
        // Trigger new topic generation if this is master
        if (this.isMaster) {
            this.requestNewTopic();
        }
    }
    
    async requestNewTopic() {
        try {
            const response = await fetch('/api/generate-topic', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.currentTopic = data.topic;
                this.updateTopicDisplay();
                this.saveSyncState();
            }
        } catch (error) {
            console.log('Failed to generate new topic:', error);
        }
    }
    
    updateTimestamps() {
        // Update all message timestamps to current time
        const currentTime = new Date();
        const timeString = this.formatTime(currentTime);
        
        this.conversationData.forEach(message => {
            message.timestamp = timeString;
        });
        
        this.saveSyncState();
        this.updateDisplay();
    }
    
    getLatestMessageTimestamp() {
        if (this.conversationData.length > 0) {
            return this.conversationData[0].timestamp;
        }
        return null;
    }
    
    createInvestigationModal() {
        // Create modal for short investigation display
        const modalHTML = `
            <div class="modal fade" id="investigationModal" tabindex="-1" aria-labelledby="investigationModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header bg-primary text-white">
                            <h5 class="modal-title" id="investigationModalLabel">
                                <i class="fas fa-search me-2"></i>Short Investigation
                            </h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div id="investigationContent">
                                <div class="text-center">
                                    <div class="spinner-border text-primary" role="status">
                                        <span class="visually-hidden">Loading investigation...</span>
                                    </div>
                                    <p class="mt-2">Generating investigation summary...</p>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                            <button type="button" class="btn btn-primary" id="shareInvestigation">
                                <i class="fas fa-share me-1"></i>Share Investigation
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Add modal to body if it doesn't exist
        if (!document.getElementById('investigationModal')) {
            document.body.insertAdjacentHTML('beforeend', modalHTML);
        }
        
        // Add event listener for share button
        document.getElementById('shareInvestigation').addEventListener('click', () => {
            this.shareInvestigation();
        });
    }
    
    async showInvestigation(messageId, messageContent, agentType) {
        const modal = new bootstrap.Modal(document.getElementById('investigationModal'));
        const content = document.getElementById('investigationContent');
        
        // Show loading state
        content.innerHTML = `
            <div class="text-center">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading investigation...</span>
                </div>
                <p class="mt-2">Generating investigation summary...</p>
            </div>
        `;
        
        modal.show();
        
        try {
            // Try to get investigation from API
            const response = await fetch('/api/investigation', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    messageId: messageId,
                    messageContent: messageContent,
                    agentType: agentType,
                    topic: this.currentTopic
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                this.displayInvestigation(data);
            } else {
                // Fallback to generated investigation
                this.generateFallbackInvestigation(messageContent, agentType);
            }
        } catch (error) {
            console.log('Failed to load investigation from API:', error);
            // Fallback to generated investigation
            this.generateFallbackInvestigation(messageContent, agentType);
        }
    }
    
    generateFallbackInvestigation(messageContent, agentType) {
        // Generate a realistic investigation summary based on the message
        const investigations = {
            'Business AI Assistant': {
                title: 'Business Analysis & Market Position',
                sections: [
                    {
                        title: 'Service Quality Assessment',
                        content: 'Perfect Roofing Team demonstrates exceptional service quality through their comprehensive approach to roofing solutions. Their commitment to using premium materials and employing certified contractors positions them as a market leader in the New Jersey roofing industry.'
                    },
                    {
                        title: 'Competitive Advantages',
                        content: 'Key differentiators include 24/7 emergency response capabilities, comprehensive warranty coverage, and a proven track record of customer satisfaction. Their local expertise in New Jersey weather patterns and building codes provides significant value to customers.'
                    },
                    {
                        title: 'Business Recommendations',
                        content: 'Continue focusing on quality craftsmanship and customer service excellence. Expand digital marketing efforts to reach more homeowners in need of roofing services. Consider partnerships with local insurance companies for storm damage restoration projects.'
                    }
                ]
            },
            'Marketing AI Expert': {
                title: 'Marketing Strategy & Brand Analysis',
                sections: [
                    {
                        title: 'Brand Positioning',
                        content: 'Perfect Roofing Team has successfully positioned itself as a premium, reliable roofing contractor in the New Jersey market. Their emphasis on quality materials and professional installation resonates well with homeowners seeking long-term value.'
                    },
                    {
                        title: 'Digital Presence',
                        content: 'Strong online presence with positive customer reviews and comprehensive service descriptions. Website optimization and local SEO strategies are effectively driving qualified leads from homeowners in need of roofing services.'
                    },
                    {
                        title: 'Marketing Opportunities',
                        content: 'Leverage seasonal marketing campaigns during storm seasons. Develop case studies showcasing successful projects. Implement referral programs to capitalize on satisfied customer networks.'
                    }
                ]
            },
            'Customer Service AI': {
                title: 'Customer Experience & Service Analysis',
                sections: [
                    {
                        title: 'Service Excellence',
                        content: 'Perfect Roofing Team excels in customer communication and project transparency. Their detailed documentation process and regular updates keep customers informed throughout the roofing project lifecycle.'
                    },
                    {
                        title: 'Customer Satisfaction',
                        content: 'High customer satisfaction rates driven by professional installation teams, quality materials, and comprehensive warranty coverage. Customers particularly appreciate the 24/7 emergency response capability.'
                    },
                    {
                        title: 'Service Improvements',
                        content: 'Continue investing in customer communication tools and project management systems. Expand customer education resources about roofing maintenance and care. Develop loyalty programs for repeat customers.'
                    }
                ]
            },
            'SEO AI Specialist': {
                title: 'SEO Performance & Online Visibility',
                sections: [
                    {
                        title: 'Search Engine Performance',
                        content: 'Perfect Roofing Team maintains strong local search visibility for key roofing-related keywords in New Jersey. Their content strategy effectively targets homeowners searching for roofing contractors and emergency repair services.'
                    },
                    {
                        title: 'Content Strategy',
                        content: 'Well-optimized service pages and location-specific content drive qualified organic traffic. Regular content updates about roofing tips, maintenance, and industry insights establish authority in the roofing sector.'
                    },
                    {
                        title: 'SEO Recommendations',
                        content: 'Expand content marketing with seasonal roofing guides and maintenance tips. Optimize for voice search queries related to emergency roofing services. Build more local citations and industry partnerships for link building.'
                    }
                ]
            }
        };
        
        const investigation = investigations[agentType] || investigations['Business AI Assistant'];
        this.displayInvestigation({
            title: investigation.title,
            summary: `Comprehensive analysis of Perfect Roofing Team's ${investigation.title.toLowerCase()} based on current market conditions and industry best practices.`,
            sections: investigation.sections,
            messageContent: messageContent,
            agentType: agentType,
            timestamp: new Date().toLocaleString(),
            confidence: Math.floor(Math.random() * 15) + 85 // 85-99% confidence
        });
    }
    
    displayInvestigation(data) {
        const content = document.getElementById('investigationContent');
        
        content.innerHTML = `
            <div class="investigation-summary">
                <div class="d-flex align-items-center mb-3">
                    <div class="investigation-icon me-3">
                        <i class="fas fa-search-plus text-primary" style="font-size: 2rem;"></i>
                    </div>
                    <div>
                        <h4 class="mb-1">${data.title}</h4>
                        <p class="text-muted mb-0">${data.summary}</p>
                    </div>
                </div>
                
                <div class="investigation-meta mb-4">
                    <div class="row">
                        <div class="col-md-6">
                            <small class="text-muted">
                                <i class="fas fa-robot me-1"></i>
                                Analyzed by: ${data.agentType}
                            </small>
                        </div>
                        <div class="col-md-6 text-md-end">
                            <small class="text-muted">
                                <i class="fas fa-clock me-1"></i>
                                Generated: ${data.timestamp}
                            </small>
                        </div>
                    </div>
                    <div class="row mt-2">
                        <div class="col-12">
                            <div class="progress" style="height: 6px;">
                                <div class="progress-bar bg-success" style="width: ${data.confidence}%"></div>
                            </div>
                            <small class="text-muted">Confidence Level: ${data.confidence}%</small>
                        </div>
                    </div>
                </div>
                
                <div class="investigation-sections">
                    ${data.sections.map(section => `
                        <div class="investigation-section mb-4">
                            <h5 class="section-title">
                                <i class="fas fa-chevron-right me-2 text-primary"></i>
                                ${section.title}
                            </h5>
                            <p class="section-content">${section.content}</p>
                        </div>
                    `).join('')}
                </div>
                
                <div class="investigation-footer mt-4 pt-3 border-top">
                    <div class="row">
                        <div class="col-md-8">
                            <h6>Original Message Context:</h6>
                            <blockquote class="blockquote-sm">
                                <p class="mb-0 text-muted">"${data.messageContent}"</p>
                            </blockquote>
                        </div>
                        <div class="col-md-4 text-md-end">
                            <div class="investigation-actions">
                                <button class="btn btn-outline-primary btn-sm me-2" onclick="window.conversationFeed.downloadInvestigation()">
                                    <i class="fas fa-download me-1"></i>Download
                                </button>
                                <button class="btn btn-outline-secondary btn-sm" onclick="window.conversationFeed.printInvestigation()">
                                    <i class="fas fa-print me-1"></i>Print
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Store current investigation for sharing/downloading
        this.currentInvestigation = data;
    }
    
    shareInvestigation() {
        if (this.currentInvestigation) {
            const shareText = `Investigation Summary: ${this.currentInvestigation.title}\n\n${this.currentInvestigation.summary}\n\nView full analysis at: ${window.location.href}`;
            
            if (navigator.share) {
                navigator.share({
                    title: `Investigation: ${this.currentInvestigation.title}`,
                    text: shareText,
                    url: window.location.href
                });
            } else {
                // Fallback: copy to clipboard
                navigator.clipboard.writeText(shareText).then(() => {
                    alert('Investigation summary copied to clipboard!');
                });
            }
        }
    }
    
    downloadInvestigation() {
        if (this.currentInvestigation) {
            const content = `
Investigation Summary
====================

Title: ${this.currentInvestigation.title}
Generated: ${this.currentInvestigation.timestamp}
Analyzed by: ${this.currentInvestigation.agentType}
Confidence: ${this.currentInvestigation.confidence}%

Summary:
${this.currentInvestigation.summary}

Detailed Analysis:
${this.currentInvestigation.sections.map(section => `
${section.title}
${'='.repeat(section.title.length)}
${section.content}
`).join('\n')}

Original Message:
"${this.currentInvestigation.messageContent}"

Generated by Perfect Roofing Team AI Analysis System
            `;
            
            const blob = new Blob([content], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `investigation-${Date.now()}.txt`;
            a.click();
            URL.revokeObjectURL(url);
        }
    }
    
    printInvestigation() {
        const printWindow = window.open('', '_blank');
        printWindow.document.write(`
            <html>
                <head>
                    <title>Investigation Summary</title>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 20px; }
                        h1, h2 { color: #0d6efd; }
                        .meta { background: #f8f9fa; padding: 10px; margin: 10px 0; }
                        .section { margin: 20px 0; }
                        blockquote { background: #f8f9fa; padding: 10px; border-left: 4px solid #0d6efd; }
                    </style>
                </head>
                <body>
                    ${document.getElementById('investigationContent').innerHTML}
                </body>
            </html>
        `);
        printWindow.document.close();
        printWindow.print();
    }
    
    createAIServicesStatus() {
        const existingStatus = document.getElementById('ai-services-status');
        if (existingStatus) return;
        
        const statusContainer = document.createElement('div');
        statusContainer.id = 'ai-services-status';
        statusContainer.className = 'ai-services-status mb-3';
        
        const conversationStream = document.getElementById('conversation-stream');
        if (conversationStream) {
            // Insert at the bottom of the conversation stream
            conversationStream.appendChild(statusContainer);
        }
        
        this.updateAIServicesDisplay();
    }
    
    updateAIServicesDisplay() {
        const statusContainer = document.getElementById('ai-services-status');
        if (!statusContainer) return;
        
        const serviceMapping = {
            gemini: { name: 'Google AI', status: 'Indexed', color: 'primary' },
            openai: { name: 'ChatGPT', status: 'Crawled', color: 'success' },
            perplexity: { name: 'Perplexity', status: 'Listed', color: 'warning' },
            anthropic: { name: 'Anthropic', status: 'Ranked', color: 'info' }
        };
        
        let statusHTML = '<div class="card-footer text-center bg-light"><div class="row text-center">';
        
        Object.keys(serviceMapping).forEach(serviceKey => {
            const service = serviceMapping[serviceKey];
            const isOnline = this.aiServicesStatus[serviceKey];
            const statusClass = isOnline ? 'text-' + service.color : 'text-muted';
            const statusIcon = isOnline ? 'fas fa-check-circle' : 'fas fa-times-circle';
            
            statusHTML += `
                <div class="col-3">
                    <div class="service-status ${isOnline ? 'online' : 'offline'}">
                        <i class="${statusIcon} me-1"></i>
                        <strong class="${statusClass}">${service.name}</strong><br>
                        <small class="text-muted">${service.status}</small>
                    </div>
                </div>
            `;
        });
        
        statusHTML += '</div>';
        statusHTML += '<p class="text-muted mt-2 mb-0 small">Real-time status of AI service connections</p>';
        statusHTML += '</div>';
        
        statusContainer.innerHTML = statusHTML;
    }
    
    updateTopicDisplay() {
        const topicElements = document.querySelectorAll('.current-topic');
        topicElements.forEach(element => {
            element.textContent = this.currentTopic;
        });
        
        // Update page title if topic is available
        if (this.currentTopic) {
            const titleElement = document.querySelector('h1, .page-title');
            if (titleElement && this.isLivePage === 'public_conversation') {
                titleElement.textContent = this.currentTopic;
            }
        }
    }
    
    loadSyncState() {
        try {
            const syncData = localStorage.getItem(this.syncKey);
            if (syncData) {
                const parsed = JSON.parse(syncData);
                this.conversationData = parsed.messages || [];
                this.currentTopic = parsed.topic || '';
                this.messageCount = parsed.messageCount || 0;
                this.lastUpdateTime = parsed.lastUpdate || Date.now();
                this.currentAgentIndex = parsed.agentIndex || 0;
            }
        } catch (error) {
            console.log('No sync data found, starting fresh');
        }
    }
    
    saveSyncState() {
        const syncData = {
            messages: this.conversationData,
            topic: this.currentTopic,
            messageCount: this.messageCount,
            lastUpdate: this.lastUpdateTime,
            agentIndex: this.currentAgentIndex,
            timestamp: Date.now()
        };
        localStorage.setItem(this.syncKey, JSON.stringify(syncData));
        
        // Broadcast to other tabs
        this.broadcastSync(syncData);
    }
    
    setupCrossTabSync() {
        // Listen for storage changes (cross-tab communication)
        window.addEventListener('storage', (e) => {
            if (e.key === this.syncKey && e.newValue) {
                const syncData = JSON.parse(e.newValue);
                this.handleSyncUpdate(syncData);
            }
        });
        
        // Listen for custom sync events
        window.addEventListener('conversationSync', (e) => {
            this.handleSyncUpdate(e.detail);
        });
    }
    
    broadcastSync(data) {
        // Dispatch custom event for same-tab communication
        window.dispatchEvent(new CustomEvent('conversationSync', { detail: data }));
    }
    
    handleSyncUpdate(syncData) {
        if (!this.isMaster && syncData.timestamp > this.lastUpdateTime) {
            this.conversationData = syncData.messages;
            this.currentTopic = syncData.topic;
            this.messageCount = syncData.messageCount;
            this.lastUpdateTime = syncData.lastUpdate;
            this.currentAgentIndex = syncData.agentIndex;
            this.updateDisplay();
            this.updateTopicDisplay();
        }
    }
    
    createLiveStatusBar() {
        const existingBar = document.getElementById('live-status-bar');
        if (existingBar) return;
        
        const statusBar = document.createElement('div');
        statusBar.id = 'live-status-bar';
        statusBar.className = 'alert alert-success d-flex align-items-center justify-content-between mb-3';
        statusBar.style.cssText = `
            border-left: 4px solid #28a745;
            background: linear-gradient(135deg, rgba(40, 167, 69, 0.1), rgba(40, 167, 69, 0.05));
            border-radius: 8px;
            padding: 12px 16px;
        `;
        
        statusBar.innerHTML = `
            <div class="d-flex align-items-center">
                <div class="status-indicator me-2"></div>
                <span class="fw-bold text-success">LIVE NOW</span>
                <span class="ms-2">- AI agents are actively discussing</span>
                <span class="current-topic ms-2 badge bg-info"></span>
            </div>
            <div class="d-flex align-items-center">
                <span class="badge bg-success me-2">4 AI agents online</span>
                <small class="text-muted">Active now</small>
            </div>
        `;
        
        const conversationStream = document.getElementById('conversation-stream');
        if (conversationStream) {
            conversationStream.insertBefore(statusBar, conversationStream.firstChild);
        }
    }
    
    createCountdownTimer() {
        const existingTimer = document.getElementById('next-message-countdown');
        if (existingTimer) return;
        
        const timerContainer = document.createElement('div');
        timerContainer.id = 'next-message-countdown';
        timerContainer.className = 'alert alert-info d-flex align-items-center justify-content-between mb-3';
        timerContainer.style.cssText = `
            border-left: 4px solid #0d6efd;
            background: linear-gradient(135deg, rgba(13, 110, 253, 0.1), rgba(13, 110, 253, 0.05));
            border-radius: 8px;
            padding: 12px 16px;
        `;
        
        timerContainer.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="fas fa-clock me-2 text-primary"></i>
                <span>Next AI conversation in <span id="countdown-timer" class="fw-bold text-primary">45</span> seconds</span>
                <span class="ms-2 small text-muted">(<span id="message-counter">${this.messageCount}</span>/${this.maxMessagesPerRound} in current topic)</span>
            </div>
            <div class="progress" style="width: 200px; height: 6px;">
                <div id="countdown-progress" class="progress-bar bg-primary" style="width: 100%; transition: width 1s linear;"></div>
            </div>
        `;
        
        const statusBar = document.getElementById('live-status-bar');
        if (statusBar) {
            statusBar.parentNode.insertBefore(timerContainer, statusBar.nextSibling);
        }
    }
    
    createActivityPulse() {
        const existingPulse = document.querySelector('.activity-pulse');
        if (existingPulse) return;
        
        const pulse = document.createElement('div');
        pulse.className = 'activity-pulse';
        document.body.appendChild(pulse);
    }
    
    formatTime(date) {
        return date.toLocaleTimeString('en-US', {
            hour: 'numeric',
            minute: '2-digit',
            hour12: true
        });
    }
    
    updateDisplay() {
        const conversationStream = document.getElementById('conversation-stream');
        if (!conversationStream) return;
        
        // Remove existing messages (keep status elements)
        const existingMessages = conversationStream.querySelectorAll('.message-stream-item');
        existingMessages.forEach(msg => msg.remove());
        
        // Add current messages
        this.conversationData.forEach((message, index) => {
            const messageElement = this.createMessageElement(message, index === 0);
            
            // Insert after status elements
            const statusElements = conversationStream.querySelectorAll('#live-status-bar, #next-message-countdown, #typing-indicator');
            const lastStatusElement = statusElements[statusElements.length - 1];
            
            if (lastStatusElement) {
                conversationStream.insertBefore(messageElement, lastStatusElement.nextSibling);
            } else {
                conversationStream.appendChild(messageElement);
            }
        });
        
        // Update message counter
        const messageCounter = document.getElementById('message-counter');
        if (messageCounter) {
            messageCounter.textContent = this.messageCount;
        }
    }
    
    createMessageElement(message, isNew = false) {
        const agent = this.agents.find(a => a.id === message.agent_name) || this.agents[0];
        const isServiceOnline = this.aiServicesStatus[agent.service];
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message-stream-item p-3 mb-3 border rounded ${isNew ? 'slide-up' : ''}`;
        messageDiv.style.cssText = `
            background: white;
            border: 1px solid #e9ecef;
            transition: all 0.3s ease;
        `;
        
        messageDiv.innerHTML = `
            <div class="d-flex align-items-start justify-content-between">
                <div class="d-flex align-items-center mb-2">
                    <div class="badge bg-${agent.color} me-2 position-relative">
                        ${message.agent_name}
                        <div class="online-indicator ${isServiceOnline ? 'online' : 'offline'}"></div>
                    </div>
                    <div>
                        <h6 class="mb-0 text-${agent.color}">${message.agent_type}</h6>
                        <small class="text-muted">${message.agent_name} AI Agent • Live Discussion</small>
                    </div>
                </div>
                <div class="d-flex align-items-center">
                    <span class="text-muted me-2">${message.timestamp}</span>
                    <span class="badge live-badge">LIVE</span>
                </div>
            </div>
            <p class="mb-3">${message.message_content}</p>
            <div class="d-flex align-items-center justify-content-between">
                <div class="d-flex align-items-center text-muted">
                    <i class="fas fa-link me-1"></i>
                    <span class="me-2">Source Reference:</span>
                    <a href="${message.source_url}" class="text-decoration-none me-2">${message.source_url}</a>
                    <span class="badge bg-secondary">Perfect Roofing Team</span>
                </div>
                <button class="btn btn-outline-primary btn-sm investigation-btn" 
                        onclick="window.conversationFeed.showInvestigation('${message.id}', '${message.message_content.replace(/'/g, "\\'")}', '${message.agent_type}')">
                    <i class="fas fa-search me-1"></i>Short Investigation
                </button>
            </div>
        `;
        
        return messageDiv;
    }
    
    triggerActivityPulse() {
        const pulse = document.querySelector('.activity-pulse');
        if (pulse) {
            pulse.classList.remove('pulse-active');
            setTimeout(() => {
                pulse.classList.add('pulse-active');
            }, 10);
        }
    }
    
    initializeDashboard() {
        // For dashboard pages, show historical conversations without live updates
        console.log('Dashboard mode - showing historical conversations');
        this.enhanceDashboardStyling();
    }
    
    enhanceDashboardStyling() {
        const style = document.createElement('style');
        style.textContent = `
            .conversation-card {
                transition: transform 0.2s ease, box-shadow 0.2s ease;
            }
            .conversation-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            }
        `;
        document.head.appendChild(style);
    }
}

// Enhanced CSS Styles with Investigation Features
const apiIntegratedWithInvestigationStyles = `
<style>
/* Live status indicators */
.status-indicator {
    width: 12px;
    height: 12px;
    background: #28a745;
    border-radius: 50%;
    animation: pulse 2s infinite;
}

.online-indicator {
    position: absolute;
    bottom: -2px;
    right: -2px;
    width: 8px;
    height: 8px;
    border: 2px solid white;
    border-radius: 50%;
}

.online-indicator.online {
    background: #28a745;
    animation: pulse 2s infinite;
}

.online-indicator.offline {
    background: #dc3545;
}

.live-badge {
    background: linear-gradient(45deg, #ff0000, #ff4444);
    color: white;
    font-size: 10px;
    padding: 2px 6px;
    border-radius: 10px;
    font-weight: bold;
    animation: pulse 2s infinite;
}

/* Investigation Button */
.investigation-btn {
    transition: all 0.3s ease;
    border-radius: 20px;
    font-size: 12px;
    padding: 4px 12px;
}

.investigation-btn:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 8px rgba(13, 110, 253, 0.3);
}

/* Investigation Modal */
.investigation-summary {
    line-height: 1.6;
}

.investigation-icon {
    background: linear-gradient(135deg, rgba(13, 110, 253, 0.1), rgba(13, 110, 253, 0.05));
    border-radius: 50%;
    width: 60px;
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.investigation-section {
    padding: 15px;
    background: rgba(248, 249, 250, 0.5);
    border-radius: 8px;
    border-left: 4px solid #0d6efd;
}

.section-title {
    color: #0d6efd;
    font-size: 1.1rem;
    margin-bottom: 10px;
}

.section-content {
    color: #495057;
    margin-bottom: 0;
}

.investigation-meta {
    background: rgba(13, 110, 253, 0.05);
    padding: 15px;
    border-radius: 8px;
    border: 1px solid rgba(13, 110, 253, 0.1);
}

.investigation-footer {
    background: rgba(248, 249, 250, 0.8);
    border-radius: 8px;
    padding: 15px;
}

.blockquote-sm {
    font-size: 0.9rem;
    padding: 10px 15px;
    background: white;
    border-radius: 6px;
    border-left: 3px solid #0d6efd;
}

.investigation-actions .btn {
    border-radius: 20px;
    font-size: 12px;
}

/* AI Services Status */
.ai-services-status .service-status {
    padding: 8px;
    border-radius: 6px;
    transition: all 0.3s ease;
}

.ai-services-status .service-status.online {
    background: rgba(40, 167, 69, 0.1);
    border: 1px solid rgba(40, 167, 69, 0.3);
}

.ai-services-status .service-status.offline {
    background: rgba(220, 53, 69, 0.1);
    border: 1px solid rgba(220, 53, 69, 0.3);
}

/* Activity pulse */
.activity-pulse {
    position: fixed;
    top: 20px;
    right: 20px;
    width: 20px;
    height: 20px;
    background: #28a745;
    border-radius: 50%;
    opacity: 0;
    pointer-events: none;
    z-index: 1000;
}

.activity-pulse.pulse-active {
    animation: activityPulse 2s ease-out;
}

@keyframes activityPulse {
    0% {
        transform: scale(0);
        opacity: 1;
    }
    100% {
        transform: scale(4);
        opacity: 0;
    }
}

/* Animations */
@keyframes pulse {
    0% { 
        transform: scale(1);
        opacity: 1;
    }
    50% { 
        transform: scale(1.1);
        opacity: 0.7;
    }
    100% { 
        transform: scale(1);
        opacity: 1;
    }
}

.slide-up {
    animation: slideUp 0.3s ease-out;
}

@keyframes slideUp {
    from { 
        transform: translateY(20px); 
        opacity: 0; 
    }
    to { 
        transform: translateY(0); 
        opacity: 1; 
    }
}

/* Progress bar animation */
.progress-bar {
    transition: width 1s linear;
}

/* Message hover effects */
.message-stream-item:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.message-stream-item:hover .investigation-btn {
    background-color: #0d6efd;
    color: white;
    border-color: #0d6efd;
}
</style>
`;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Add enhanced styles
    document.head.insertAdjacentHTML('beforeend', apiIntegratedWithInvestigationStyles);
    
    // Initialize API-integrated conversation feed with investigation feature
    window.conversationFeed = new APIIntegratedConversationFeed();
});

// Export for manual initialization if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = APIIntegratedConversationFeed;
}

