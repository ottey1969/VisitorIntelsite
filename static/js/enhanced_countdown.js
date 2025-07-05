/**
 * Enhanced Countdown Timer with Local Timezone Support
 * Automatically converts server time to user's local timezone
 */

class EnhancedCountdownTimer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.isRunning = false;
        this.interval = null;
        this.initializeTimer();
    }
    
    initializeTimer() {
        if (!this.container) return;
        
        // Create countdown display elements
        this.container.innerHTML = `
            <div class="enhanced-countdown-container">
                <div class="countdown-header">
                    <h4 id="countdown-header-text">Next AI Conversation</h4>
                    <div class="countdown-status">
                        <span class="status-badge waiting">Waiting</span>
                    </div>
                </div>
                <div class="countdown-display">
                    <div class="time-display">
                        <span class="countdown-time" id="countdown-time">--:--</span>
                        <small style="font-size: 0.8em; color: rgba(255,255,255,0.8); margin-left: 8px;">min:sec</small>
                    </div>
                    <div class="time-info">
                        <small>Local time: <span id="local-time">--:--:--</span></small>
                        <br>
                        <small>Next conversation: <span id="next-conversation-time">Loading...</span></small>
                    </div>
                </div>
                <div class="countdown-progress">
                    <div class="progress-bar">
                        <div class="progress-fill" id="progress-fill"></div>
                    </div>
                    <small><span id="remaining-text">Loading countdown...</span></small>
                </div>
            </div>
        `;
        
        // Add CSS styles
        this.addStyles();
        
        // Start the timer
        this.startTimer();
    }
    
    addStyles() {
        if (document.getElementById('enhanced-countdown-styles')) return;
        
        const style = document.createElement('style');
        style.id = 'enhanced-countdown-styles';
        style.textContent = `
            .enhanced-countdown-container {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 12px;
                text-align: center;
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                margin: 20px 0;
            }
            
            .countdown-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
            }
            
            .countdown-header h4 {
                margin: 0;
                font-weight: 600;
            }
            
            .status-badge {
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 500;
                text-transform: uppercase;
            }
            
            .status-badge.waiting {
                background: rgba(255,255,255,0.2);
                border: 1px solid rgba(255,255,255,0.3);
            }
            
            .status-badge.active {
                background: #4CAF50;
                border: 1px solid #45a049;
            }
            
            .countdown-display {
                margin: 20px 0;
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
            
            .countdown-progress {
                margin-top: 20px;
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
    
    async fetchCountdownData() {
        try {
            const response = await fetch('/api/system-status');
            if (!response.ok) throw new Error('Failed to fetch system status');
            
            const data = await response.json();
            if (data) {
                
                // Calculate remaining seconds
                let remaining_seconds = 0;
                if (data.next_conversation_time && data.next_conversation_time !== null) {
                    try {
                        const nextTime = new Date(data.next_conversation_time);
                        const now = new Date();
                        if (!isNaN(nextTime.getTime())) {
                            remaining_seconds = Math.max(0, Math.floor((nextTime - now) / 1000));
                        }
                    } catch (e) {
                        console.warn('Error parsing next conversation time:', e);
                        remaining_seconds = 0;
                    }
                }
                
                // Return countdown data in expected format
                return {
                    remaining_seconds: remaining_seconds,
                    state: data.conversation_status || (data.conversation_active ? 'active' : 'waiting'),
                    next_time_local: data.next_conversation_time,
                    conversation_active: data.conversation_active || false
                };
            } else {
                throw new Error('Invalid response format');
            }
        } catch (error) {
            console.error('Error fetching countdown:', error);
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
    
    formatRemainingText(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        
        if (hours > 0) {
            return `${hours}h ${minutes}m ${secs}s remaining`;
        } else if (minutes > 0) {
            return `${minutes} minutes ${secs} seconds remaining`;
        } else {
            return `${seconds} seconds remaining`;
        }
    }
    
    updateDisplay(data) {
        if (!data || data.error) {
            document.getElementById('countdown-time').textContent = 'Error';
            document.getElementById('remaining-text').textContent = 'Unable to load countdown';
            return;
        }
        
        const remainingSeconds = data.remaining_seconds;
        const countdownTime = document.getElementById('countdown-time');
        const localTime = document.getElementById('local-time');
        const nextConversationTime = document.getElementById('next-conversation-time');
        const remainingText = document.getElementById('remaining-text');
        const progressFill = document.getElementById('progress-fill');
        const statusBadge = this.container.querySelector('.status-badge');
        const headerText = document.getElementById('countdown-header-text');
        
        // Update countdown time
        countdownTime.textContent = this.formatTime(remainingSeconds);
        
        // Update current local time
        const now = new Date();
        localTime.textContent = now.toLocaleTimeString();
        
        // Update next conversation time (convert from server to local)
        if (data.next_time_local) {
            const nextTime = new Date(data.next_time_local);
            nextConversationTime.textContent = nextTime.toLocaleTimeString();
        }
        
        // Update remaining text
        remainingText.textContent = this.formatRemainingText(remainingSeconds);
        
        // Update progress bar (30 minutes = 1800 seconds total)
        const totalSeconds = 30 * 60; // 30 minutes
        const progress = Math.max(0, Math.min(100, ((totalSeconds - remainingSeconds) / totalSeconds) * 100));
        progressFill.style.width = `${progress}%`;
        
        // Update status based on conversation_active or conversation_status
        const isActive = data.conversation_active || data.state === 'active';
        if (isActive) {
            statusBadge.textContent = 'ACTIVE';
            statusBadge.className = 'status-badge active';
            headerText.textContent = 'AI Conversation Active';
        } else {
            statusBadge.textContent = 'WAITING';
            statusBadge.className = 'status-badge waiting';
            headerText.textContent = 'Next AI Conversation';
        }
    }
    
    async updateCountdown() {
        const data = await this.fetchCountdownData();
        this.updateDisplay(data);
        
        // If conversation is starting soon (less than 10 seconds), prepare for active state
        if (data && data.remaining_seconds <= 10 && data.remaining_seconds > 0) {
            console.log('Conversation starting soon...');
        }
        
        // If conversation should be active, refresh more frequently
        if (data && data.state === 'active') {
            this.interval = setTimeout(() => this.updateCountdown(), 5000); // 5 seconds for active
        } else {
            this.interval = setTimeout(() => this.updateCountdown(), 1000); // 1 second for waiting
        }
    }
    
    startTimer() {
        if (this.isRunning) return;
        
        this.isRunning = true;
        this.updateCountdown();
    }
    
    stopTimer() {
        this.isRunning = false;
        if (this.interval) {
            clearTimeout(this.interval);
            this.interval = null;
        }
    }
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Look for countdown containers
    const countdownContainer = document.getElementById('enhanced-countdown');
    if (countdownContainer) {
        window.enhancedCountdown = new EnhancedCountdownTimer('enhanced-countdown');
    }
});

// Export for manual initialization
window.EnhancedCountdownTimer = EnhancedCountdownTimer;