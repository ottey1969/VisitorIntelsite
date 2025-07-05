/**
 * Mood Color Manager - Dynamic color palette system for conversations
 * Automatically applies mood-based color themes to conversations
 */

class MoodColorManager {
    constructor() {
        this.currentConversationId = null;
        this.currentPalette = null;
        this.themeStyleElement = null;
        this.isEnabled = true;
        
        // Initialize theme style element
        this.initializeThemeElement();
        
        console.log('[MoodColor] Mood Color Manager initialized');
    }
    
    /**
     * Initialize or get the theme style element
     */
    initializeThemeElement() {
        // Check if theme element already exists
        this.themeStyleElement = document.getElementById('mood-color-theme');
        
        if (!this.themeStyleElement) {
            // Create new style element
            this.themeStyleElement = document.createElement('style');
            this.themeStyleElement.id = 'mood-color-theme';
            this.themeStyleElement.type = 'text/css';
            document.head.appendChild(this.themeStyleElement);
            console.log('[MoodColor] Theme style element created');
        }
    }
    
    /**
     * Apply color theme for a specific conversation
     */
    async applyConversationTheme(conversationId) {
        if (!this.isEnabled || !conversationId) {
            console.log('[MoodColor] Theme application skipped - disabled or no conversation ID');
            return;
        }
        
        try {
            console.log(`[MoodColor] Applying theme for conversation ${conversationId}`);
            
            // Fetch color palette
            const palette = await this.fetchColorPalette(conversationId);
            if (!palette) {
                console.warn('[MoodColor] No palette received, using default');
                return;
            }
            
            // Apply the theme
            this.currentConversationId = conversationId;
            this.currentPalette = palette;
            
            // Generate and apply CSS
            const cssContent = this.generateThemeCSS(palette);
            this.applyCSS(cssContent);
            
            // Update UI indicators
            this.updateMoodIndicators(palette);
            
            console.log(`[MoodColor] Theme applied - Mood: ${palette.mood}, Intensity: ${palette.intensity}%`);
            
        } catch (error) {
            console.error('[MoodColor] Error applying theme:', error);
        }
    }
    
    /**
     * Fetch color palette from API
     */
    async fetchColorPalette(conversationId) {
        try {
            const response = await fetch(`/api/conversation/${conversationId}/colors`);
            const data = await response.json();
            
            if (data.success) {
                return data.palette;
            } else {
                console.error('[MoodColor] API error:', data.error);
                return null;
            }
        } catch (error) {
            console.error('[MoodColor] Fetch error:', error);
            return null;
        }
    }
    
    /**
     * Generate CSS from color palette
     */
    generateThemeCSS(palette) {
        return `
/* Mood Color Theme - ${palette.mood} (${palette.intensity}% intensity) */
:root {
    --mood-primary: ${palette.primary};
    --mood-secondary: ${palette.secondary};
    --mood-accent: ${palette.accent};
    --mood-background: ${palette.background};
    --mood-text: ${palette.text};
    --mood-primary-light: ${palette.primary_light};
    --mood-primary-dark: ${palette.primary_dark};
    --mood-secondary-light: ${palette.secondary_light};
}

/* Apply theme to conversation elements */
.conversation-container {
    background: linear-gradient(135deg, ${palette.background}aa, ${palette.primary_light}22);
    border: 1px solid ${palette.primary_light};
}

.message-item {
    background: ${palette.background}dd;
    border-left: 3px solid ${palette.primary};
    box-shadow: 0 2px 8px ${palette.primary}22;
}

.message-item:hover {
    background: ${palette.background};
    border-left-color: ${palette.accent};
    transform: translateX(2px);
}

.message-item.message-even {
    background: ${palette.secondary_light}33;
}

.agent-avatar {
    background: linear-gradient(135deg, ${palette.primary}, ${palette.secondary});
    border: 2px solid ${palette.primary_light};
}

.agent-name {
    color: ${palette.primary_dark};
}

.message-meta {
    color: ${palette.text}aa;
}

.conversation-header {
    background: linear-gradient(135deg, ${palette.primary}, ${palette.secondary});
    color: white;
}

.conversation-stats .badge {
    background: ${palette.accent};
    color: white;
}

/* Enhanced countdown styling */
.enhanced-countdown {
    border: 2px solid ${palette.primary_light};
    background: linear-gradient(135deg, ${palette.background}, ${palette.primary_light}22);
}

.progress-fill {
    background: linear-gradient(90deg, ${palette.primary}, ${palette.secondary});
}

.status-badge {
    background: ${palette.accent};
    color: white;
}

/* Button theming */
.btn-primary {
    background: linear-gradient(135deg, ${palette.primary}, ${palette.secondary});
    border-color: ${palette.primary};
}

.btn-primary:hover {
    background: linear-gradient(135deg, ${palette.primary_dark}, ${palette.primary});
    border-color: ${palette.primary_dark};
}

/* Mood indicator styling */
.mood-indicator {
    display: inline-flex;
    align-items: center;
    padding: 4px 8px;
    border-radius: 12px;
    background: ${palette.accent}22;
    color: ${palette.text};
    font-size: 0.85em;
    font-weight: 500;
}

.mood-indicator::before {
    content: '';
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: ${palette.accent};
    margin-right: 6px;
}
`;
    }
    
    /**
     * Apply CSS to the theme element
     */
    applyCSS(cssContent) {
        if (this.themeStyleElement) {
            this.themeStyleElement.textContent = cssContent;
        }
    }
    
    /**
     * Update mood indicators in the UI
     */
    updateMoodIndicators(palette) {
        // Remove existing mood indicators
        document.querySelectorAll('.mood-indicator').forEach(el => el.remove());
        
        // Add mood indicator to conversation header
        const conversationHeader = document.querySelector('.conversation-header');
        if (conversationHeader && palette.mood) {
            const moodIndicator = document.createElement('span');
            moodIndicator.className = 'mood-indicator ms-2';
            moodIndicator.textContent = this.formatMoodName(palette.mood);
            moodIndicator.title = `Conversation mood: ${palette.mood} (${palette.intensity}% intensity)`;
            
            conversationHeader.appendChild(moodIndicator);
        }
        
        // Add mood indicator to live stats if present
        const liveStats = document.querySelector('.live-stats-showcase');
        if (liveStats && palette.mood) {
            const statsContainer = liveStats.querySelector('.row') || liveStats;
            const moodCol = document.createElement('div');
            moodCol.className = 'col-md-3';
            moodCol.innerHTML = `
                <div class="text-center">
                    <h6 class="mb-1">Conversation Mood</h6>
                    <div class="mood-indicator">
                        ${this.formatMoodName(palette.mood)}
                    </div>
                </div>
            `;
            statsContainer.appendChild(moodCol);
        }
    }
    
    /**
     * Format mood name for display
     */
    formatMoodName(mood) {
        const moodEmojis = {
            'positive': '😊 Positive',
            'energetic': '⚡ Energetic', 
            'calm': '😌 Calm',
            'professional': '💼 Professional',
            'urgent': '🚨 Urgent',
            'trustworthy': '🛡️ Trustworthy'
        };
        
        return moodEmojis[mood] || `✨ ${mood.charAt(0).toUpperCase() + mood.slice(1)}`;
    }
    
    /**
     * Get current mood analysis for a conversation
     */
    async getMoodAnalysis(conversationId) {
        try {
            const response = await fetch(`/api/conversation/${conversationId}/mood`);
            const data = await response.json();
            
            if (data.success) {
                return data;
            } else {
                console.error('[MoodColor] Mood analysis error:', data.error);
                return null;
            }
        } catch (error) {
            console.error('[MoodColor] Mood analysis fetch error:', error);
            return null;
        }
    }
    
    /**
     * Enable/disable mood color system
     */
    setEnabled(enabled) {
        this.isEnabled = enabled;
        if (!enabled) {
            this.clearTheme();
        }
        console.log(`[MoodColor] Mood color system ${enabled ? 'enabled' : 'disabled'}`);
    }
    
    /**
     * Clear current theme
     */
    clearTheme() {
        if (this.themeStyleElement) {
            this.themeStyleElement.textContent = '';
        }
        
        // Remove mood indicators
        document.querySelectorAll('.mood-indicator').forEach(el => el.remove());
        
        this.currentConversationId = null;
        this.currentPalette = null;
        
        console.log('[MoodColor] Theme cleared');
    }
    
    /**
     * Get current palette information
     */
    getCurrentPalette() {
        return this.currentPalette;
    }
    
    /**
     * Check if mood colors are enabled
     */
    isThemeEnabled() {
        return this.isEnabled;
    }
}

// Global mood color manager instance
let moodColorManager = null;

/**
 * Initialize mood color manager
 */
function initializeMoodColorManager() {
    if (!moodColorManager) {
        moodColorManager = new MoodColorManager();
    }
    return moodColorManager;
}

/**
 * Apply mood theme to current conversation
 */
async function applyMoodTheme(conversationId) {
    const manager = initializeMoodColorManager();
    await manager.applyConversationTheme(conversationId);
}

/**
 * Toggle mood color system
 */
function toggleMoodColors(enabled) {
    const manager = initializeMoodColorManager();
    manager.setEnabled(enabled);
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeMoodColorManager();
});

// Export for global access
window.MoodColorManager = MoodColorManager;
window.moodColorManager = moodColorManager;
window.applyMoodTheme = applyMoodTheme;
window.toggleMoodColors = toggleMoodColors;