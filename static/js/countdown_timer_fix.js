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

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Only start if countdown container exists
    if (document.getElementById('enhanced-countdown')) {
        window.robustCountdown = new RobustCountdownTimer();
        window.robustCountdown.start();
    }
});

// Export for manual use
window.RobustCountdownTimer = RobustCountdownTimer;