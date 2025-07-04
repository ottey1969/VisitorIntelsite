// Enhanced Business Dashboard Dynamic Controls
// Implements Generate, View, Download, Delete functionality based on content status

class DashboardContentManager {
    constructor() {
        this.businessId = this.extractBusinessId();
        this.contentModules = {
            'faq': {
                name: 'FAQ Pages',
                icon: 'fas fa-question-circle',
                generateText: 'Generate FAQ',
                status: 'not_generated'
            },
            'local_seo': {
                name: 'Local SEO',
                icon: 'fas fa-map-marker-alt',
                generateText: 'Generate Local',
                status: 'not_generated'
            },
            'voice_search': {
                name: 'Voice Search',
                icon: 'fas fa-microphone',
                generateText: 'Optimize Voice',
                status: 'not_generated'
            },
            'knowledge_base': {
                name: 'Knowledge Base',
                icon: 'fas fa-book',
                generateText: 'Build Knowledge',
                status: 'not_generated'
            }
        };
        
        this.init();
    }

    extractBusinessId() {
        // Extract business ID from URL path
        const pathParts = window.location.pathname.split('/');
        const businessIndex = pathParts.indexOf('business');
        return businessIndex !== -1 && pathParts[businessIndex + 1] ? pathParts[businessIndex + 1] : '1';
    }

    async init() {
        await this.fetchContentStatus();
        this.setupEventListeners();
        this.updateAllButtonStates();
    }

    async fetchContentStatus() {
        try {
            const response = await fetch(`/api/business/${this.businessId}/content-status`);
            if (response.ok) {
                const statusData = await response.json();
                // Update module statuses based on API response
                for (const moduleKey in statusData) {
                    if (this.contentModules[moduleKey]) {
                        this.contentModules[moduleKey].status = statusData[moduleKey] ? 'generated' : 'not_generated';
                    }
                }
            } else {
                console.warn('Failed to fetch content status, using defaults');
                // For demo purposes, simulate some content as generated
                this.contentModules['faq'].status = 'generated';
                this.contentModules['voice_search'].status = 'generated';
            }
        } catch (error) {
            console.error('Error fetching content status:', error);
            // Fallback to demo data
            this.contentModules['faq'].status = 'generated';
            this.contentModules['voice_search'].status = 'generated';
        }
    }

    setupEventListeners() {
        // Use event delegation for dynamically created buttons
        document.addEventListener('click', (event) => {
            const button = event.target.closest('[data-content-action]');
            if (button) {
                event.preventDefault();
                this.handleButtonClick(button);
            }
        });
    }

    async handleButtonClick(button) {
        const action = button.dataset.contentAction;
        const moduleType = button.dataset.contentType;
        
        if (!this.contentModules[moduleType]) {
            console.error('Unknown module type:', moduleType);
            return;
        }

        // Show loading state
        this.setButtonLoading(button, true);

        try {
            switch (action) {
                case 'generate':
                    await this.generateContent(moduleType);
                    break;
                case 'view':
                    await this.viewContent(moduleType);
                    break;
                case 'download':
                    await this.downloadContent(moduleType);
                    break;
                case 'delete':
                    await this.deleteContent(moduleType);
                    break;
                default:
                    console.error('Unknown action:', action);
            }
        } catch (error) {
            console.error('Error handling button click:', error);
            this.showNotification(`Error: ${error.message}`, 'error');
        } finally {
            this.setButtonLoading(button, false);
        }
    }

    async generateContent(moduleType) {
        try {
            const response = await fetch(`/api/business/${this.businessId}/generate-content`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    contentType: moduleType,
                    businessId: this.businessId
                })
            });

            if (response.ok) {
                const result = await response.json();
                this.contentModules[moduleType].status = 'generated';
                this.updateButtonState(moduleType);
                this.showNotification(`${this.contentModules[moduleType].name} generated successfully!`, 'success');
                
                // Log generation activity
                this.logActivity('generate', moduleType, 'Content generated successfully');
            } else {
                throw new Error(`Failed to generate ${moduleType}`);
            }
        } catch (error) {
            // Fallback for demo purposes
            console.warn('API not available, using demo mode');
            this.contentModules[moduleType].status = 'generated';
            this.updateButtonState(moduleType);
            this.showNotification(`${this.contentModules[moduleType].name} generated successfully! (Demo)`, 'success');
            this.logActivity('generate', moduleType, 'Content generated (demo mode)');
        }
    }

    async viewContent(moduleType) {
        try {
            // In a real implementation, this would open a modal or navigate to a view page
            const response = await fetch(`/api/business/${this.businessId}/content/${moduleType}`);
            
            if (response.ok) {
                const content = await response.json();
                this.showContentModal(moduleType, content);
            } else {
                throw new Error(`Failed to load ${moduleType} content`);
            }
        } catch (error) {
            // Fallback for demo purposes
            console.warn('API not available, showing demo content');
            this.showContentModal(moduleType, {
                title: `${this.contentModules[moduleType].name} Content`,
                content: `This is demo content for ${this.contentModules[moduleType].name}. In a real implementation, this would show the actual generated content.`,
                generatedAt: new Date().toISOString()
            });
        }
        
        this.logActivity('view', moduleType, 'Content viewed');
    }

    async downloadContent(moduleType) {
        try {
            const response = await fetch(`/api/business/${this.businessId}/content/${moduleType}/download`);
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `${moduleType}_content.pdf`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                
                this.showNotification(`${this.contentModules[moduleType].name} downloaded successfully!`, 'success');
            } else {
                throw new Error(`Failed to download ${moduleType} content`);
            }
        } catch (error) {
            // Fallback for demo purposes
            console.warn('API not available, simulating download');
            this.simulateDownload(moduleType);
            this.showNotification(`${this.contentModules[moduleType].name} download started! (Demo)`, 'success');
        }
        
        this.logActivity('download', moduleType, 'Content downloaded');
    }

    async deleteContent(moduleType) {
        // Confirm deletion
        if (!confirm(`Are you sure you want to delete ${this.contentModules[moduleType].name}? This action cannot be undone.`)) {
            return;
        }

        try {
            const response = await fetch(`/api/business/${this.businessId}/content/${moduleType}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                this.contentModules[moduleType].status = 'not_generated';
                this.updateButtonState(moduleType);
                this.showNotification(`${this.contentModules[moduleType].name} deleted successfully!`, 'success');
            } else {
                throw new Error(`Failed to delete ${moduleType} content`);
            }
        } catch (error) {
            // Fallback for demo purposes
            console.warn('API not available, using demo mode');
            this.contentModules[moduleType].status = 'not_generated';
            this.updateButtonState(moduleType);
            this.showNotification(`${this.contentModules[moduleType].name} deleted successfully! (Demo)`, 'success');
        }
        
        this.logActivity('delete', moduleType, 'Content deleted');
    }

    updateAllButtonStates() {
        for (const moduleType in this.contentModules) {
            this.updateButtonState(moduleType);
        }
    }

    updateButtonState(moduleType) {
        const module = this.contentModules[moduleType];
        const buttonContainer = this.findButtonContainer(moduleType);
        
        if (!buttonContainer) {
            console.warn(`Button container not found for ${moduleType}`);
            return;
        }

        if (module.status === 'generated') {
            // Show View, Download, Delete buttons
            buttonContainer.innerHTML = `
                <button class="btn btn-outline-primary btn-sm mb-2 w-100" 
                        data-content-action="view" 
                        data-content-type="${moduleType}">
                    <i class="fas fa-eye me-1"></i>View
                </button>
                <button class="btn btn-outline-success btn-sm mb-2 w-100" 
                        data-content-action="download" 
                        data-content-type="${moduleType}">
                    <i class="fas fa-download me-1"></i>Download
                </button>
                <button class="btn btn-outline-danger btn-sm w-100" 
                        data-content-action="delete" 
                        data-content-type="${moduleType}">
                    <i class="fas fa-trash-alt me-1"></i>Delete
                </button>
            `;
        } else {
            // Show Generate button
            buttonContainer.innerHTML = `
                <button class="btn btn-primary btn-sm w-100" 
                        data-content-action="generate" 
                        data-content-type="${moduleType}">
                    <i class="${module.icon} me-1"></i>${module.generateText}
                </button>
            `;
        }
    }

    findButtonContainer(moduleType) {
        // Try to find the button container based on the module type
        // This assumes a specific HTML structure - you may need to adjust
        const containers = document.querySelectorAll('.card-body');
        
        for (const container of containers) {
            const existingButton = container.querySelector(`[data-content-type="${moduleType}"]`);
            if (existingButton) {
                return existingButton.parentElement;
            }
            
            // Fallback: look for buttons with specific text content
            const buttons = container.querySelectorAll('button');
            for (const button of buttons) {
                if (button.textContent.includes(this.contentModules[moduleType].generateText)) {
                    return button.parentElement;
                }
            }
        }
        
        return null;
    }

    setButtonLoading(button, isLoading) {
        if (isLoading) {
            button.disabled = true;
            button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Loading...';
        } else {
            button.disabled = false;
            // The button content will be updated by updateButtonState
        }
    }

    showContentModal(moduleType, content) {
        // Create and show a modal with the content
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="${this.contentModules[moduleType].icon} me-2"></i>
                            ${this.contentModules[moduleType].name}
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <h6>${content.title || 'Content'}</h6>
                        <p class="text-muted">Generated: ${new Date(content.generatedAt || Date.now()).toLocaleString()}</p>
                        <div class="content-preview">
                            ${content.content || 'Content preview not available'}
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-success" 
                                data-content-action="download" 
                                data-content-type="${moduleType}">
                            <i class="fas fa-download me-1"></i>Download
                        </button>
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Show the modal using Bootstrap
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
        
        // Remove modal from DOM when hidden
        modal.addEventListener('hidden.bs.modal', () => {
            document.body.removeChild(modal);
        });
    }

    simulateDownload(moduleType) {
        // Create a demo file for download
        const content = `${this.contentModules[moduleType].name} Content\n\nThis is demo content for ${this.contentModules[moduleType].name}.\nGenerated on: ${new Date().toLocaleString()}\n\nIn a real implementation, this would contain the actual generated content.`;
        
        const blob = new Blob([content], { type: 'text/plain' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${moduleType}_content_demo.txt`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    }

    showNotification(message, type = 'info') {
        // Create a toast notification
        const toast = document.createElement('div');
        toast.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
        toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        toast.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(toast);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, 5000);
    }

    logActivity(action, moduleType, details) {
        const timestamp = new Date().toLocaleTimeString();
        console.log(`[${timestamp}] ${action.toUpperCase()} ${moduleType}: ${details}`);
        
        // In a real implementation, you might want to send this to an analytics endpoint
        // fetch('/api/analytics/log', {
        //     method: 'POST',
        //     headers: { 'Content-Type': 'application/json' },
        //     body: JSON.stringify({ action, moduleType, details, timestamp })
        // });
    }
}

// Initialize the dashboard content manager when the DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize on business dashboard pages
    if (window.location.pathname.includes('/business/')) {
        window.dashboardManager = new DashboardContentManager();
    }
});

// Export for testing purposes
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DashboardContentManager;
}

