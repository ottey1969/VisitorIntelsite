// Business Dashboard Controls with Real Backend Integration
// Perfect Roofing Team - Real Business Content Management

class DashboardContentManager {
    constructor() {
        this.config = {
            BACKEND_URL: '',
            API_TIMEOUT: 15000,
            RETRY_ATTEMPTS: 3
        };
        
        this.businessId = this.extractBusinessId();
        this.contentModules = {
            faq: {
                name: 'FAQ Pages',
                description: 'AI-generated FAQ content targeting search queries',
                icon: 'fas fa-question-circle',
                status: 'not_generated'
            },
            local: {
                name: 'Local SEO',
                description: 'Location-specific pages for better local search',
                icon: 'fas fa-map-marker-alt',
                status: 'not_generated'
            },
            voice: {
                name: 'Voice Search',
                description: 'Content optimized for voice search queries',
                icon: 'fas fa-microphone',
                status: 'not_generated'
            },
            knowledge: {
                name: 'Knowledge Base',
                description: 'Industry expertise articles and important guides',
                icon: 'fas fa-book',
                status: 'not_generated'
            }
        };
        
        this.init();
    }
    
    init() {
        console.log('[Dashboard] Initializing Content Manager for business:', this.businessId);
        this.setupEventListeners();
        this.loadContentStatus();
        this.loadShowcaseUrl();
    }
    
    extractBusinessId() {
        // Extract business ID from URL path
        const pathMatch = window.location.pathname.match(/\/business\/(\d+)/);
        return pathMatch ? pathMatch[1] : '1'; // Default to 1 if not found
    }
    
    setupEventListeners() {
        // Use event delegation for dynamic buttons
        document.addEventListener('click', (e) => {
            const target = e.target.closest('button');
            if (!target) return;
            
            const action = target.dataset.action;
            const contentType = target.dataset.contentType;
            
            if (action && contentType) {
                e.preventDefault();
                this.handleAction(action, contentType, target);
            }
        });
    }
    
    async handleAction(action, contentType, button) {
        console.log(`[Dashboard] Handling action: ${action} for ${contentType}`);
        
        switch (action) {
            case 'generate':
                await this.generateContent(contentType, button);
                break;
            case 'view':
                await this.viewContent(contentType);
                break;
            case 'download':
                await this.downloadContent(contentType);
                break;
            case 'delete':
                await this.deleteContent(contentType, button);
                break;
        }
    }
    
    async loadContentStatus() {
        console.log('[Dashboard] Loading content status...');
        
        try {
            const response = await this.makeAPICall(`/api/business/${this.businessId}/content-status`);
            if (response.success) {
                // Update module status from backend
                Object.keys(this.contentModules).forEach(type => {
                    if (response.content_status[type]) {
                        this.contentModules[type].status = response.content_status[type].status;
                        this.contentModules[type].generated_at = response.content_status[type].generated_at;
                    }
                });
                
                this.renderAllModules();
                console.log('[Dashboard] Content status loaded successfully');
            }
        } catch (error) {
            console.error('[Dashboard] Error loading content status:', error);
            this.showNotification('Unable to load content status. Using offline mode.', 'warning');
            this.renderAllModules(); // Render with default status
        }
    }
    
    async loadShowcaseUrl() {
        try {
            const response = await this.makeAPICall(`/api/business/${this.businessId}/showcase-url`);
            if (response.success) {
                this.updateShowcaseUrl(response.showcase_url);
            }
        } catch (error) {
            console.error('[Dashboard] Error loading showcase URL:', error);
        }
    }
    
    updateShowcaseUrl(url) {
        const showcaseInput = document.querySelector('#showcase-url-input, .showcase-url-field');
        const copyButton = document.querySelector('#copy-url-btn, .copy-url-button');
        
        if (showcaseInput) {
            showcaseInput.value = url;
            showcaseInput.style.display = 'block';
        }
        
        if (copyButton) {
            copyButton.style.display = 'block';
            copyButton.onclick = () => {
                navigator.clipboard.writeText(url).then(() => {
                    this.showNotification('Showcase URL copied to clipboard!', 'success');
                });
            };
        }
    }
    
    renderAllModules() {
        Object.keys(this.contentModules).forEach(type => {
            this.renderModule(type);
        });
    }
    
    renderModule(contentType) {
        const module = this.contentModules[contentType];
        const container = document.querySelector(`[data-content-type="${contentType}"], #${contentType}-module`);
        
        if (!container) {
            console.warn(`[Dashboard] No container found for ${contentType}`);
            return;
        }
        
        // Update status indicator
        const statusIndicator = container.querySelector('.status-indicator');
        if (statusIndicator) {
            statusIndicator.className = `status-indicator status-${module.status}`;
        }
        
        // Update button container
        const buttonContainer = container.querySelector('.button-container, .module-actions');
        if (buttonContainer) {
            buttonContainer.innerHTML = this.generateButtons(contentType, module);
        }
        
        // Update generated date if available
        const dateElement = container.querySelector('.generated-date');
        if (dateElement && module.generated_at) {
            dateElement.textContent = `Generated: ${new Date(module.generated_at).toLocaleDateString()}`;
            dateElement.style.display = 'block';
        }
    }
    
    generateButtons(contentType, module) {
        if (module.status === 'not_generated') {
            return `
                <button class="btn btn-primary" 
                        data-action="generate" 
                        data-content-type="${contentType}">
                    <i class="${module.icon} me-1"></i>Generate ${module.name}
                </button>
            `;
        } else if (module.status === 'generated') {
            return `
                <div class="btn-group" role="group">
                    <button class="btn btn-outline-primary" 
                            data-action="view" 
                            data-content-type="${contentType}">
                        <i class="fas fa-eye me-1"></i>View
                    </button>
                    <button class="btn btn-outline-success" 
                            data-action="download" 
                            data-content-type="${contentType}">
                        <i class="fas fa-download me-1"></i>Download
                    </button>
                    <button class="btn btn-outline-danger" 
                            data-action="delete" 
                            data-content-type="${contentType}">
                        <i class="fas fa-trash me-1"></i>Delete
                    </button>
                </div>
            `;
        } else if (module.status === 'generating') {
            return `
                <button class="btn btn-primary" disabled>
                    <span class="spinner-border spinner-border-sm me-2"></span>
                    Generating...
                </button>
            `;
        }
    }
    
    async generateContent(contentType, button) {
        console.log(`[Dashboard] Generating ${contentType} content...`);
        
        // Update UI to show generating state
        this.contentModules[contentType].status = 'generating';
        this.renderModule(contentType);
        
        try {
            const response = await this.makeAPICall(
                `/api/business/${this.businessId}/generate-content`,
                'POST',
                { content_type: contentType }
            );
            
            if (response.success) {
                // Update status to generated
                this.contentModules[contentType].status = 'generated';
                this.contentModules[contentType].generated_at = response.generated_at;
                
                this.renderModule(contentType);
                this.showNotification(response.message, 'success');
                
                console.log(`[Dashboard] ${contentType} generated successfully`);
            } else {
                throw new Error(response.error || 'Generation failed');
            }
        } catch (error) {
            console.error(`[Dashboard] Error generating ${contentType}:`, error);
            
            // Revert status
            this.contentModules[contentType].status = 'not_generated';
            this.renderModule(contentType);
            
            this.showNotification(`Failed to generate ${this.contentModules[contentType].name}. Please try again.`, 'error');
        }
    }
    
    async viewContent(contentType) {
        console.log(`[Dashboard] Viewing ${contentType} content...`);
        
        try {
            const response = await this.makeAPICall(`/api/business/${this.businessId}/content/${contentType}`);
            
            if (response.success) {
                this.displayContentModal(contentType, response.content);
            } else {
                throw new Error(response.error || 'Failed to load content');
            }
        } catch (error) {
            console.error(`[Dashboard] Error viewing ${contentType}:`, error);
            this.showNotification(`Unable to load ${this.contentModules[contentType].name}`, 'error');
        }
    }
    
    displayContentModal(contentType, content) {
        const module = this.contentModules[contentType];
        
        // Create or get modal
        let modal = document.getElementById('content-view-modal');
        if (!modal) {
            modal = this.createContentModal();
        }
        
        // Populate modal
        const modalTitle = modal.querySelector('.modal-title');
        const modalBody = modal.querySelector('.modal-body');
        
        modalTitle.textContent = `${module.name} - Perfect Roofing Team`;
        
        modalBody.innerHTML = `
            <div class="content-preview">
                <div class="content-header mb-3">
                    <h5>${content.title}</h5>
                    <div class="content-meta">
                        <span class="badge bg-primary me-2">
                            <i class="${module.icon} me-1"></i>${module.name}
                        </span>
                        <small class="text-muted">
                            Generated: ${new Date(this.contentModules[contentType].generated_at).toLocaleString()}
                        </small>
                    </div>
                </div>
                
                <div class="content-body">
                    <pre class="content-text">${content.content}</pre>
                </div>
                
                ${content.metadata ? `
                    <div class="content-metadata mt-4 pt-3 border-top">
                        <h6>Content Metrics</h6>
                        <div class="row">
                            <div class="col-md-4">
                                <strong>Word Count:</strong> ${content.metadata.word_count}
                            </div>
                            <div class="col-md-4">
                                <strong>SEO Score:</strong> ${content.metadata.seo_score}/100
                            </div>
                            <div class="col-md-4">
                                <strong>Keywords:</strong> ${content.metadata.target_keywords.length}
                            </div>
                        </div>
                        <div class="mt-2">
                            <strong>Target Keywords:</strong> 
                            ${content.metadata.target_keywords.map(kw => `<span class="badge bg-secondary me-1">${kw}</span>`).join('')}
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
        
        // Store current content for download
        this.currentViewContent = { contentType, content };
        
        // Show modal
        const bootstrapModal = new bootstrap.Modal(modal);
        bootstrapModal.show();
    }
    
    createContentModal() {
        const modalHTML = `
            <div class="modal fade" id="content-view-modal" tabindex="-1">
                <div class="modal-dialog modal-xl">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Content Preview</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <!-- Content will be populated by JavaScript -->
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-success" id="modal-download-btn">
                                <i class="fas fa-download me-1"></i>Download
                            </button>
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        // Add download handler
        document.getElementById('modal-download-btn').addEventListener('click', () => {
            if (this.currentViewContent) {
                this.downloadContent(this.currentViewContent.contentType);
            }
        });
        
        return document.getElementById('content-view-modal');
    }
    
    async downloadContent(contentType) {
        console.log(`[Dashboard] Downloading ${contentType} content...`);
        
        try {
            const response = await fetch(`${this.config.BACKEND_URL}/api/business/${this.businessId}/content/${contentType}/download`);
            
            if (response.ok) {
                const blob = await response.blob();
                const url = URL.createObjectURL(blob);
                
                // Get filename from response headers or create default
                const contentDisposition = response.headers.get('content-disposition');
                let filename = `perfect_roofing_${contentType}_${Date.now()}.md`;
                
                if (contentDisposition) {
                    const filenameMatch = contentDisposition.match(/filename="(.+)"/);
                    if (filenameMatch) {
                        filename = filenameMatch[1];
                    }
                }
                
                // Create download link
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                a.click();
                
                URL.revokeObjectURL(url);
                
                this.showNotification(`${this.contentModules[contentType].name} downloaded successfully`, 'success');
            } else {
                throw new Error(`Download failed: ${response.statusText}`);
            }
        } catch (error) {
            console.error(`[Dashboard] Error downloading ${contentType}:`, error);
            this.showNotification(`Failed to download ${this.contentModules[contentType].name}`, 'error');
        }
    }
    
    async deleteContent(contentType, button) {
        const module = this.contentModules[contentType];
        
        // Show confirmation dialog
        const confirmed = confirm(`Are you sure you want to delete the ${module.name}? This action cannot be undone.`);
        if (!confirmed) return;
        
        console.log(`[Dashboard] Deleting ${contentType} content...`);
        
        try {
            const response = await this.makeAPICall(
                `/api/business/${this.businessId}/content/${contentType}`,
                'DELETE'
            );
            
            if (response.success) {
                // Update status
                this.contentModules[contentType].status = 'not_generated';
                this.contentModules[contentType].generated_at = null;
                
                this.renderModule(contentType);
                this.showNotification(response.message, 'success');
                
                console.log(`[Dashboard] ${contentType} deleted successfully`);
            } else {
                throw new Error(response.error || 'Deletion failed');
            }
        } catch (error) {
            console.error(`[Dashboard] Error deleting ${contentType}:`, error);
            this.showNotification(`Failed to delete ${module.name}`, 'error');
        }
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
                console.log(`[Dashboard API] ${method} ${endpoint} (attempt ${attempt})`);
                const response = await fetch(url, options);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const result = await response.json();
                console.log(`[Dashboard API] ${method} ${endpoint} - Success`);
                return result;
                
            } catch (error) {
                lastError = error;
                console.warn(`[Dashboard API] ${method} ${endpoint} - Attempt ${attempt} failed:`, error.message);
                
                if (attempt < this.config.RETRY_ATTEMPTS) {
                    // Wait before retry
                    await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
                }
            }
        }
        
        console.error(`[Dashboard API] ${method} ${endpoint} - All attempts failed:`, lastError);
        throw lastError;
    }
    
    showNotification(message, type = 'info') {
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : type === 'success' ? 'success' : type === 'warning' ? 'warning' : 'info'} border-0`;
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
            toastContainer.style.zIndex = '9999';
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
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize on business dashboard pages
    if (window.location.pathname.includes('/business/')) {
        console.log('[Dashboard] Initializing Dashboard Content Manager...');
        window.dashboardManager = new DashboardContentManager();
    }
});

// CSS for dashboard styling
const style = document.createElement('style');
style.textContent = `
    .status-indicator {
        position: absolute;
        top: 10px;
        right: 10px;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        border: 2px solid white;
        box-shadow: 0 0 0 1px rgba(0,0,0,0.1);
    }
    
    .status-not_generated {
        background-color: #dc3545;
    }
    
    .status-generated {
        background-color: #28a745;
    }
    
    .status-generating {
        background-color: #ffc107;
        animation: pulse 2s infinite;
    }
    
    .content-card {
        transition: transform 0.2s, box-shadow 0.2s;
        position: relative;
    }
    
    .content-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15) !important;
    }
    
    .btn-group .btn {
        flex: 1;
    }
    
    .content-text {
        white-space: pre-wrap;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-size: 0.9em;
        line-height: 1.6;
        background: #f8f9fa;
        padding: 20px;
        border-radius: 8px;
        border: 1px solid #e9ecef;
        max-height: 400px;
        overflow-y: auto;
    }
    
    .content-meta {
        display: flex;
        align-items: center;
        gap: 10px;
        flex-wrap: wrap;
    }
    
    .generated-date {
        font-size: 0.8em;
        color: #6c757d;
        margin-top: 5px;
        display: none;
    }
    
    .showcase-url-field {
        font-family: monospace;
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 4px;
        padding: 8px 12px;
        font-size: 0.9em;
    }
    
    .copy-url-button {
        margin-left: 10px;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
`;
document.head.appendChild(style);

console.log('[Dashboard] Script loaded successfully - Ready for real backend integration');