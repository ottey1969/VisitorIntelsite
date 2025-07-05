/**
 * Fixed Countdown Timer - Robust implementation with proper error handling
 * Only initializes when required DOM elements are present
 */
class RobustCountdownTimer {
    constructor() {
        this.isRunning = false;
        this.interval = null;
        this.requiredElements = null;
        this.retryCount = 0;
        this.maxRetries = 10;
    }

    checkElements() {
        const container = document.getElementById('enhanced-countdown');
        if (!container) return false;

        // If container is empty, create the countdown HTML structure
        if (!container.innerHTML.trim()) {
            this.createCountdownHTML(container);
        }

        const elements = {
            countdownTime: document.getElementById('countdown-time'),
            localTime: document.getElementById('local-time'),
            nextConversationTime: document.getElementById('next-conversation-time'),
            remainingText: document.getElementById('remaining-text'),
            progressFill: document.getElementById('progress-fill'),
            statusBadge: container.querySelector('.status-badge'),
            headerText: document.getElementById('countdown-header-text')
        };

        // Check if all required elements exist
        const allElementsExist = Object.values(elements).every(el => el !== null);
        
        if (allElementsExist) {
            this.requiredElements = elements;
            return true;
        }
        
        return false;
    }

    createCountdownHTML(container) {
        container.innerHTML = `
            <div class="countdown-widget bg-gradient-primary text-white rounded-4 shadow-lg p-4 mb-4">
                <div class="text-center">
                    <h5 class="fw-bold mb-3">
                        <span id="countdown-header-text">AI Conversation Status</span>
                        <span class="status-badge ms-2 px-3 py-1 rounded-pill bg-white text-primary">⏸️ WAITING</span>
                    </h5>
                    
                    <div class="countdown-display">
                        <div class="time-display" id="countdown-time">00:00</div>
                        <div class="time-info">
                            <div><strong>Local Time:</strong> <span id="local-time">Loading...</span></div>
                            <div><strong>Next Event:</strong> <span id="next-conversation-time">Calculating...</span></div>
                        </div>
                    </div>
                    
                    <div id="remaining-text" class="mt-3">Initializing countdown...</div>
                    
                    <div class="countdown-progress mt-3">
                        <div class="progress-bar">
                            <div id="progress-fill" class="progress-fill"></div>
                        </div>
                        <small class="opacity-75">21-minute conversation cycles (16 messages + 5 min break)</small>
                    </div>
                </div>
            </div>
        `;
        
        // Add necessary CSS
        this.addCountdownStyles();
    }

    addCountdownStyles() {
        if (document.getElementById('countdown-styles')) return;
        
        const style = document.createElement('style');
        style.id = 'countdown-styles';
        style.textContent = `
            .countdown-widget {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }
            
            .status-badge.active {
                background: #dc3545 !important;
                color: white !important;
                animation: pulse 2s infinite;
            }
            
            .status-badge.waiting {
                background: #ffc107 !important;
                color: #000 !important;
            }
            
            @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.7; }
                100% { opacity: 1; }
            }
            
            .time-display {
                font-size: 2.5em;
                font-weight: bold;
                margin-bottom: 10px;
                font-family: 'Courier New', monospace;
            }
            
            .time-info {
                opacity: 0.9;
                line-height: 1.4;
            }
            
            .progress-bar {
                background: rgba(255,255,255,0.2);
                height: 8px;
                border-radius: 4px;
                overflow: hidden;
                margin-bottom: 8px;
            }
            
            .progress-fill {
                background: rgba(255,255,255,0.8);
                height: 100%;
                border-radius: 4px;
                transition: width 1s ease;
                width: 0%;
            }
        `;
        document.head.appendChild(style);
    }

    async fetchSystemStatus() {
        try {
            const response = await fetch('/api/system-status');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.warn('Failed to fetch system status:', error.message);
            return null;
        }
    }

    formatTime(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        
        if (hours > 0) {
            return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        } else {
            return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        }
    }

    updateDisplay(data) {
        if (!this.requiredElements || !data) return;

        const {
            countdownTime,
            localTime,
            nextConversationTime,
            remainingText,
            progressFill,
            statusBadge,
            headerText
        } = this.requiredElements;

        try {
            // Calculate remaining seconds
            let remainingSeconds = 0;
            if (data.next_conversation_time) {
                const nextTime = new Date(data.next_conversation_time);
                const now = new Date();
                if (!isNaN(nextTime.getTime())) {
                    remainingSeconds = Math.max(0, Math.floor((nextTime - now) / 1000));
                }
            }

            // Update countdown time
            countdownTime.textContent = this.formatTime(remainingSeconds);

            // Update local time
            const now = new Date();
            localTime.textContent = now.toLocaleTimeString('en-US', {
                hour: 'numeric',
                minute: '2-digit',
                second: '2-digit',
                hour12: true
            });

            // Update next conversation time
            if (data.next_conversation_time) {
                const nextTime = new Date(data.next_conversation_time);
                if (!isNaN(nextTime.getTime())) {
                    nextConversationTime.textContent = nextTime.toLocaleTimeString('en-US', {
                        hour: 'numeric',
                        minute: '2-digit',
                        hour12: true
                    });
                } else {
                    nextConversationTime.textContent = 'Calculating...';
                }
            } else {
                nextConversationTime.textContent = 'Calculating...';
            }

            // Update status and remaining text
            const isActive = data.conversation_active || data.conversation_status === 'active';
            
            if (isActive) {
                statusBadge.textContent = '🔴 LIVE';
                statusBadge.className = 'status-badge active';
                headerText.textContent = '4 AI Agents Are Having Live Discussion';
                
                if (remainingSeconds > 0) {
                    remainingText.textContent = `🤖 Next message in ${this.formatTime(remainingSeconds)}`;
                } else {
                    remainingText.textContent = '🤖 AI agents are generating the next message...';
                }
            } else {
                statusBadge.textContent = '⏸️ WAITING';
                statusBadge.className = 'status-badge waiting';
                headerText.textContent = 'Waiting for Next AI Discussion';
                
                if (remainingSeconds > 0) {
                    remainingText.textContent = `⏳ Next discussion starts in ${this.formatTime(remainingSeconds)}`;
                } else {
                    remainingText.textContent = '⏳ Preparing the next AI conversation...';
                }
            }

            // Update progress bar (21 minutes = 1260 seconds total cycle)
            const totalSeconds = 21 * 60;
            const progress = Math.max(0, Math.min(100, ((totalSeconds - remainingSeconds) / totalSeconds) * 100));
            progressFill.style.width = `${progress}%`;

        } catch (error) {
            console.warn('Error updating countdown display:', error.message);
        }
    }

    async update() {
        try {
            // Check if elements are still available
            if (!this.checkElements()) {
                this.retryCount++;
                if (this.retryCount < this.maxRetries) {
                    // Elements not ready yet, try again later
                    setTimeout(() => this.update(), 2000);
                } else {
                    // Stop trying after max retries
                    this.stop();
                }
                return;
            }

            // Reset retry count on success
            this.retryCount = 0;

            // Fetch and update data
            const data = await this.fetchSystemStatus();
            if (data) {
                this.updateDisplay(data);
            }

            // Continue updating if still running
            if (this.isRunning) {
                setTimeout(() => this.update(), 1000);
            }

        } catch (error) {
            console.warn('Countdown timer error:', error.message);
            
            // Continue with longer interval on error
            if (this.isRunning) {
                setTimeout(() => this.update(), 5000);
            }
        }
    }

    start() {
        if (this.isRunning) return;
        
        this.isRunning = true;
        this.retryCount = 0;
        this.update();
    }

    stop() {
        this.isRunning = false;
        if (this.interval) {
            clearTimeout(this.interval);
            this.interval = null;
        }
    }
}

// Initialize immediately when script loads
(function() {
    function initCountdown() {
        const container = document.getElementById('enhanced-countdown');
        if (container) {
            window.robustCountdown = new RobustCountdownTimer();
            window.robustCountdown.start();
            console.log('Countdown timer initialized successfully');
        } else {
            // Try again in 100ms if container not found
            setTimeout(initCountdown, 100);
        }
    }
    
    // Try to initialize immediately
    initCountdown();
    
    // Also try when DOM is ready as backup
    document.addEventListener('DOMContentLoaded', function() {
        if (!window.robustCountdown) {
            initCountdown();
        }
    });
})();

// Export for manual use
window.RobustCountdownTimer = RobustCountdownTimer;