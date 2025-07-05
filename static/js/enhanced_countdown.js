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
            const response = await fetch('/api/countdown');
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
        // Check if all required elements exist
        const countdownTime = document.getElementById('countdown-time');
        const localTime = document.getElementById('local-time');
        const nextConversationTime = document.getElementById('next-conversation-time');
        const remainingText = document.getElementById('remaining-text');
        const progressFill = document.getElementById('progress-fill');
        const statusBadge = this.container ? this.container.querySelector('.status-badge') : null;
        const headerText = document.getElementById('countdown-header-text');
        
        // If any essential elements are missing, return early
        if (!countdownTime || !localTime || !nextConversationTime || !remainingText || !progressFill) {
            // Silently return to avoid console spam - this is normal during initialization
            return;
        }
        
        if (!data) {
            countdownTime.textContent = '00:00';
            remainingText.textContent = 'Calculating next conversation...';
            nextConversationTime.textContent = 'Calculating...';
            return;
        }
        
        const remainingSeconds = data.remaining_seconds || 0;
        
        // Update countdown time
        countdownTime.textContent = this.formatTime(remainingSeconds);
        
        // Update current local time - use server current_time if available, otherwise local time
        if (data.current_time) {
            // Server provides current_time as ISO UTC string, convert to local time
            const currentTime = new Date(data.current_time);
            localTime.textContent = currentTime.toLocaleTimeString('en-US', { 
                hour: 'numeric', 
                minute: '2-digit', 
                second: '2-digit',
                hour12: true 
            });
        } else {
            // Fallback to local browser time
            const now = new Date();
            localTime.textContent = now.toLocaleTimeString('en-US', { 
                hour: 'numeric', 
                minute: '2-digit', 
                second: '2-digit',
                hour12: true 
            });
        }
        
        // Update status based on conversation_active or conversation_status FIRST
        const isActive = data.conversation_active || data.state === 'active';
        
        // Update next conversation time - use proper UTC to local conversion
        if (data.next_time_local && data.next_time_local !== null) {
            // Server sends next_time_local as ISO UTC string, convert to local time
            const nextTime = new Date(data.next_time_local);
            
            if (!isNaN(nextTime.getTime())) {
                // Display the next event time in user's local timezone
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
        
        // Update remaining text and countdown behavior based on status
        if (isActive) {
            // ACTIVE state - conversation is happening
            countdownTime.textContent = 'LIVE';
            countdownTime.style.color = '#28a745';
            remainingText.innerHTML = '🔴 <strong>4 AI Agents Are Having Live Discussion</strong>';
            progressFill.style.width = '100%';
            progressFill.style.background = '#28a745';
        } else {
            // WAITING state - show countdown
            countdownTime.style.color = 'white';
            
            if (remainingSeconds > 0) {
                remainingText.innerHTML = `⏳ <strong>Waiting for Next AI Discussion</strong> (${this.formatRemainingText(remainingSeconds)})`;
            } else {
                remainingText.innerHTML = '🚀 <strong>Starting New Conversation...</strong>';
            }
            
            // Update progress bar (21 minutes = 1260 seconds total cycle)
            const totalSeconds = 21 * 60; // 21 minutes (16 messages + 5 minute break)
            const progress = Math.max(0, Math.min(100, ((totalSeconds - remainingSeconds) / totalSeconds) * 100));
            progressFill.style.width = `${progress}%`;
            progressFill.style.background = 'rgba(255,255,255,0.8)';
        }
        
        // Update status badge and header text
        if (statusBadge && headerText) {
            if (isActive) {
                statusBadge.textContent = 'ACTIVE';
                statusBadge.className = 'status-badge ms-2 px-3 py-1 rounded-pill bg-success text-white';
                headerText.textContent = 'AI Conversation Active';
            } else {
                statusBadge.textContent = 'WAITING';
                statusBadge.className = 'status-badge ms-2 px-3 py-1 rounded-pill bg-white text-primary';
                headerText.textContent = 'Next AI Conversation';
            }
        }
        
        // Update remaining text with clear messaging
        if (remainingSeconds > 0) {
            if (isActive) {
                remainingText.textContent = `🤖 AI conversation in progress • Next message in ${this.formatRemainingText(remainingSeconds)}`;
            } else {
                remainingText.textContent = `⏳ Taking a short break between conversations • Next discussion starts in ${this.formatRemainingText(remainingSeconds)}`;
            }
        } else {
            if (isActive) {
                remainingText.textContent = '🤖 AI agents are generating the next message right now...';
            } else {
                remainingText.textContent = '⏳ Preparing the next AI conversation between 4 expert agents...';
            }
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