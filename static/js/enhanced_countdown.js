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
        if (!this.container) {
            console.warn('Countdown container not found');
            return;
        }
        
        console.log('Initializing countdown timer in container:', this.container.id);
        
        // HTML structure is now in the template, just start the timer
        console.log('Starting countdown timer...');
        
        // Start the timer immediately
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
            if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            
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
                    next_time_local: data.next_time_local || data.next_conversation_time,
                    conversation_active: data.conversation_active || false,
                    current_time: data.current_time || null
                };
            } else {
                throw new Error('Invalid response format');
            }
        } catch (error) {
            console.error('Error fetching countdown:', error);
            // Return a default state instead of null to prevent display errors
            return {
                remaining_seconds: 0,
                state: 'waiting',
                next_time_local: null,
                conversation_active: false,
                current_time: null
            };
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
        // Use the existing HTML structure from templates/index.html
        const countdownDisplay = document.getElementById('countdown-display');
        const localTime = document.getElementById('local-time');
        const nextEventTime = document.getElementById('next-event-time');
        const statusText = document.getElementById('status-text');
        const statusBadge = document.getElementById('status-badge');
        const nextEventText = document.getElementById('next-event-text');
        const messageCount = document.getElementById('message-count');
        const progressBar = document.getElementById('progress-bar');
        
        // If essential elements are missing, return early
        if (!countdownDisplay || !localTime || !nextEventTime) {
            return;
        }
        
        if (!data) {
            countdownDisplay.textContent = '00:00';
            nextEventTime.textContent = 'Calculating...';
            return;
        }
        
        const remainingSeconds = data.remaining_seconds || 0;
        const isActive = data.conversation_active || data.state === 'active';
        
        // Update current time - always show UTC time as requested
        const now = new Date();
        localTime.textContent = now.toISOString().split('T')[1].split('.')[0] + ' UTC';
        
        // Update status and countdown based on state
        if (isActive) {
            // ACTIVE state - conversation is happening
            if (statusText) statusText.textContent = 'AI Conversation';
            if (statusBadge) {
                statusBadge.textContent = 'ACTIVE';
                statusBadge.className = 'status-badge ms-2 px-3 py-1 rounded-pill bg-success text-white';
            }
            countdownDisplay.textContent = 'LIVE';
            countdownDisplay.style.color = '#28a745';
            if (nextEventText) nextEventText.textContent = 'Status:';
            nextEventTime.textContent = '4 AI Agents Having Live Discussion';
            if (progressBar) {
                progressBar.style.width = '100%';
                progressBar.className = 'progress-bar bg-success';
            }
        } else {
            // WAITING state - show countdown to next conversation
            if (statusText) statusText.textContent = 'Next AI Conversation';
            if (statusBadge) {
                statusBadge.textContent = 'WAITING';
                statusBadge.className = 'status-badge ms-2 px-3 py-1 rounded-pill bg-warning text-dark';
            }
            countdownDisplay.style.color = 'white';
            
            if (remainingSeconds > 0) {
                countdownDisplay.textContent = this.formatTime(remainingSeconds);
                if (nextEventText) nextEventText.textContent = 'Next Event:';
                
                // Calculate and show the actual next conversation time
                if (data.next_conversation_time) {
                    const nextTime = new Date(data.next_conversation_time);
                    if (!isNaN(nextTime.getTime())) {
                        nextEventTime.textContent = nextTime.toISOString().split('T')[1].split('.')[0] + ' UTC';
                    } else {
                        nextEventTime.textContent = 'Calculating...';
                    }
                } else {
                    nextEventTime.textContent = 'Calculating...';
                }
                
                // Update progress bar
                if (progressBar) {
                    const maxTime = 21 * 60; // 21 minutes in seconds
                    const progress = Math.max(0, Math.min(100, ((maxTime - remainingSeconds) / maxTime) * 100));
                    progressBar.style.width = progress + '%';
                    progressBar.className = 'progress-bar bg-light';
                }
            } else {
                countdownDisplay.textContent = '00:00';
                if (nextEventText) nextEventText.textContent = 'Status:';
                nextEventTime.textContent = 'Starting New Conversation...';
                if (progressBar) {
                    progressBar.style.width = '100%';
                    progressBar.className = 'progress-bar bg-warning';
                }
            }
        }
        
        // Update message count if available
        if (messageCount) {
            const currentMessages = data.current_messages || 0;
            messageCount.textContent = `${currentMessages}/16 messages`;
        }
    }
    
    async updateCountdown() {
        try {
            // First check if required elements exist
            if (!this.container || !document.getElementById('countdown-time')) {
                // Elements not available yet, wait and try again
                this.interval = setTimeout(() => this.updateCountdown(), 2000);
                return;
            }
            
            const data = await this.fetchCountdownData();
            if (data) {
                this.updateDisplay(data);
                
                // If conversation is starting soon (less than 10 seconds), prepare for active state
                if (data.remaining_seconds <= 10 && data.remaining_seconds > 0) {
                    console.log('Conversation starting soon...');
                }
                
                // If conversation should be active, refresh more frequently
                if (data.state === 'active') {
                    this.interval = setTimeout(() => this.updateCountdown(), 5000); // 5 seconds for active
                } else {
                    this.interval = setTimeout(() => this.updateCountdown(), 1000); // 1 second for waiting
                }
            } else {
                // No data received, try again with longer interval
                this.interval = setTimeout(() => this.updateCountdown(), 5000);
            }
        } catch (error) {
            // Silent error handling - elements not ready yet
            this.interval = setTimeout(() => this.updateCountdown(), 2000);
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