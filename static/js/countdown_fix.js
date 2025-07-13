/**
 * Fixed Countdown Timer System
 * Works with existing HTML structure and provides proper UTC time display
 */
class FixedCountdownTimer {
    constructor() {
        this.interval = null;
        this.isRunning = false;
        this.init();
    }
    
    init() {
        // Start the timer immediately
        this.startTimer();
    }
    
    async fetchSystemStatus() {
        try {
            const response = await fetch('/api/system-status');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            console.warn('Failed to fetch system status:', error);
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
        // Get the exact HTML elements from templates/index.html
        const countdownDisplay = document.getElementById('countdown-display');
        const localTime = document.getElementById('local-time');
        const nextEventTime = document.getElementById('next-event-time');
        const statusText = document.getElementById('status-text');
        const statusBadge = document.getElementById('status-badge');
        const nextEventText = document.getElementById('next-event-text');
        const messageCount = document.getElementById('message-count');
        const progressBar = document.getElementById('progress-bar');
        
        // If elements don't exist, return silently
        if (!countdownDisplay || !localTime || !nextEventTime) return;
        
        // Calculate remaining time
        let remainingSeconds = 0;
        let isActive = false;
        
        if (data) {
            if (data.next_conversation_time) {
                const nextTime = new Date(data.next_conversation_time);
                const now = new Date();
                remainingSeconds = Math.max(0, Math.floor((nextTime - now) / 1000));
            }
            isActive = data.conversation_active || data.conversation_status === 'active';
        }
        
        // Update current time - show UTC as requested
        const now = new Date();
        localTime.textContent = now.toISOString().substr(11, 8) + ' UTC';
        
        // Update status and display based on active/waiting state
        if (isActive) {
            // ACTIVE state
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
            // WAITING state
            if (statusText) statusText.textContent = 'Next AI Conversation';
            if (statusBadge) {
                statusBadge.textContent = 'WAITING';
                statusBadge.className = 'status-badge ms-2 px-3 py-1 rounded-pill bg-warning text-dark';
            }
            countdownDisplay.style.color = 'white';
            
            if (remainingSeconds > 0) {
                countdownDisplay.textContent = this.formatTime(remainingSeconds);
                if (nextEventText) nextEventText.textContent = 'Next Event:';
                
                // Show the actual next conversation time in UTC
                if (data && data.next_conversation_time) {
                    const nextTime = new Date(data.next_conversation_time);
                    nextEventTime.textContent = nextTime.toISOString().substr(11, 8) + ' UTC';
                } else {
                    nextEventTime.textContent = 'Calculating...';
                }
                
                // Update progress bar
                if (progressBar) {
                    const maxTime = 21 * 60; // 21 minutes total cycle
                    const progress = Math.max(0, Math.min(100, (remainingSeconds / maxTime) * 100));
                    progressBar.style.width = (100 - progress) + '%';
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
        
        // Update message count
        if (messageCount) {
            messageCount.textContent = '0/16 messages';
        }
    }
    
    async update() {
        const data = await this.fetchSystemStatus();
        this.updateDisplay(data);
    }
    
    startTimer() {
        if (this.isRunning) return;
        
        this.isRunning = true;
        
        // Initial update
        this.update();
        
        // Set interval for regular updates
        this.interval = setInterval(() => {
            this.update();
        }, 1000);
    }
    
    stopTimer() {
        this.isRunning = false;
        if (this.interval) {
            clearInterval(this.interval);
            this.interval = null;
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Wait a moment for other scripts to load
    setTimeout(() => {
        if (document.getElementById('countdown-display')) {
            window.fixedCountdownTimer = new FixedCountdownTimer();
            console.log('Fixed countdown timer initialized');
        }
    }, 1000);
});