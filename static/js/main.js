// Main JavaScript for AI Conversation Platform

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Smooth scrolling for navigation links
    initializeSmoothScrolling();
    
    // Live stats animation
    initializeLiveStats();
    
    // Conversation card animations
    initializeCardAnimations();
    
    // Form validation
    initializeFormValidation();
    
    // PayPal integration
    initializePayPal();
    
    // Auto-refresh functionality
    initializeAutoRefresh();
});

// Smooth scrolling for navigation links
function initializeSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Live stats animation
function initializeLiveStats() {
    const statsElements = document.querySelectorAll('.live-stats-card h3');
    
    // Animate numbers on page load
    statsElements.forEach(element => {
        if (element.textContent.includes('∞')) return;
        
        const targetValue = parseInt(element.textContent.replace(/,/g, ''));
        if (isNaN(targetValue)) return;
        
        animateNumber(element, 0, targetValue, 2000);
    });
    
    // Auto-update live stats every 30 seconds
    setInterval(function() {
        statsElements.forEach(element => {
            if (element.textContent.includes('∞')) return;
            
            const currentValue = parseInt(element.textContent.replace(/,/g, ''));
            if (isNaN(currentValue)) return;
            
            const increment = Math.floor(Math.random() * 5) + 1;
            const newValue = currentValue + increment;
            
            animateNumber(element, currentValue, newValue, 1000);
        });
    }, 30000);
}

// Animate number counting
function animateNumber(element, start, end, duration) {
    const startTime = performance.now();
    
    function updateNumber(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        const currentValue = Math.floor(start + (end - start) * progress);
        element.textContent = currentValue.toLocaleString();
        
        if (progress < 1) {
            requestAnimationFrame(updateNumber);
        }
    }
    
    requestAnimationFrame(updateNumber);
}

// Card animations on scroll
function initializeCardAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    // Observe all cards
    document.querySelectorAll('.feature-card, .conversation-card, .pricing-card, .dashboard-preview-card').forEach(card => {
        observer.observe(card);
    });
}

// Form validation
function initializeFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        });
    });
    
    // Real-time validation feedback
    const inputs = document.querySelectorAll('input[required], textarea[required], select[required]');
    inputs.forEach(input => {
        input.addEventListener('blur', function() {
            validateField(this);
        });
        
        input.addEventListener('input', function() {
            if (this.classList.contains('is-invalid')) {
                validateField(this);
            }
        });
    });
}

// Validate individual field
function validateField(field) {
    const isValid = field.checkValidity();
    
    field.classList.remove('is-valid', 'is-invalid');
    field.classList.add(isValid ? 'is-valid' : 'is-invalid');
    
    // Show custom error messages
    const feedback = field.parentNode.querySelector('.invalid-feedback');
    if (feedback && !isValid) {
        if (field.type === 'email') {
            feedback.textContent = 'Please enter a valid email address.';
        } else if (field.type === 'url') {
            feedback.textContent = 'Please enter a valid website URL.';
        } else if (field.hasAttribute('required') && !field.value) {
            feedback.textContent = 'This field is required.';
        }
    }
}

// PayPal integration
function initializePayPal() {
    // Package selection functionality
    window.selectPackage = function(packageId, packageName, packagePrice) {
        // Store selected package info
        window.selectedPackage = {
            id: packageId,
            name: packageName,
            price: packagePrice
        };
        
        // Show confirmation modal or redirect to payment
        showPaymentConfirmation(packageName, packagePrice);
    };
    
    // Copy share URL functionality
    window.copyShareUrl = function() {
        const urlElement = document.querySelector('code');
        if (!urlElement) return;
        
        const url = urlElement.textContent;
        
        navigator.clipboard.writeText(url).then(function() {
            showNotification('Share URL copied to clipboard!', 'success');
        }).catch(function(err) {
            console.error('Could not copy text: ', err);
            showNotification('Failed to copy URL', 'error');
        });
    };
}

// Show payment confirmation
function showPaymentConfirmation(packageName, packagePrice) {
    const modalHtml = `
        <div class="modal fade" id="paymentModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Confirm Purchase</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="text-center">
                            <i class="fab fa-paypal text-primary fa-3x mb-3"></i>
                            <h6>You're about to purchase:</h6>
                            <h4 class="text-primary">${packageName}</h4>
                            <h3 class="text-success">$${packagePrice}</h3>
                            <p class="text-muted">You'll be redirected to PayPal to complete your payment.</p>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary" onclick="processPayment()">
                            <i class="fab fa-paypal me-1"></i>Pay with PayPal
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal
    const existingModal = document.getElementById('paymentModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add new modal
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('paymentModal'));
    modal.show();
}

// Process payment (simplified for demo)
function processPayment() {
    if (!window.selectedPackage) return;
    
    // Show loading state
    const payButton = document.querySelector('#paymentModal .btn-primary');
    const originalText = payButton.innerHTML;
    payButton.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Processing...';
    payButton.disabled = true;
    
    // Simulate payment processing
    setTimeout(function() {
        // Hide modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('paymentModal'));
        modal.hide();
        
        // Show success message
        showNotification(`Payment successful! ${window.selectedPackage.name} credits have been added to your account.`, 'success');
        
        // Reset button
        payButton.innerHTML = originalText;
        payButton.disabled = false;
        
        // Refresh page after a delay
        setTimeout(function() {
            location.reload();
        }, 2000);
    }, 3000);
}

// Show notification
function showNotification(message, type = 'info') {
    const alertClass = type === 'error' ? 'alert-danger' : `alert-${type}`;
    const iconClass = type === 'error' ? 'fas fa-exclamation-triangle' : 
                     type === 'success' ? 'fas fa-check-circle' : 'fas fa-info-circle';
    
    const notificationHtml = `
        <div class="alert ${alertClass} alert-dismissible fade show position-fixed" 
             style="top: 20px; right: 20px; z-index: 9999; min-width: 300px;" role="alert">
            <i class="${iconClass} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', notificationHtml);
    
    // Auto-remove after 5 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert.position-fixed');
        alerts.forEach(alert => {
            if (alert.textContent.includes(message)) {
                alert.remove();
            }
        });
    }, 5000);
}

// Auto-refresh functionality
function initializeAutoRefresh() {
    // Auto-refresh dashboard every 2 minutes
    if (window.location.pathname.includes('/business/')) {
        setInterval(function() {
            // Only refresh if user is active (not idle)
            if (document.visibilityState === 'visible') {
                location.reload();
            }
        }, 120000); // 2 minutes
    }
}

// Conversation topic suggestions
function initializeTopicSuggestions() {
    const topicInput = document.getElementById('topic');
    if (!topicInput) return;
    
    const suggestions = [
        'Emergency Services and 24/7 Availability',
        'Quality Materials and Professional Installation',
        'Customer Service and Satisfaction Guarantee',
        'Experience and Industry Certifications',
        'Competitive Pricing and Free Estimates',
        'Storm Damage and Insurance Claims',
        'Maintenance and Warranty Services',
        'Local Community and Customer Reviews'
    ];
    
    // Create suggestions dropdown
    const suggestionsContainer = document.createElement('div');
    suggestionsContainer.className = 'topic-suggestions mt-2';
    suggestionsContainer.innerHTML = `
        <small class="text-muted">Suggested topics:</small>
        <div class="d-flex flex-wrap gap-1 mt-1">
            ${suggestions.map(suggestion => 
                `<button type="button" class="btn btn-outline-secondary btn-sm" onclick="selectTopic('${suggestion}')">${suggestion}</button>`
            ).join('')}
        </div>
    `;
    
    topicInput.parentNode.appendChild(suggestionsContainer);
    
    // Add topic selection function
    window.selectTopic = function(topic) {
        topicInput.value = topic;
        topicInput.focus();
    };
}

// Initialize topic suggestions when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeTopicSuggestions();
    initializeLiveConversationFeed();
});

// Live conversation feed animation
function initializeLiveConversationFeed() {
    const conversationStream = document.querySelector('.conversation-stream');
    if (!conversationStream) return;
    
    // Simulate new messages appearing every 30-60 seconds
    setInterval(function() {
        if (document.visibilityState === 'visible') {
            addNewLiveMessage();
            updateLiveStats();
        }
    }, Math.random() * 30000 + 30000); // Random interval between 30-60 seconds
}

function addNewLiveMessage() {
    const conversationStream = document.querySelector('.conversation-stream');
    if (!conversationStream) return;
    
    const aiAgents = [
        {
            name: 'Business AI Assistant',
            type: 'GPT',
            color: 'success',
            messages: [
                'Perfect Roofing Team delivers exceptional emergency roof repair services with licensed contractors available 24/7 throughout New Jersey. Learn more at perfectroofingteam.com/roofing-services/',
                'Quality roofing materials and professional installation make Perfect Roofing Team the preferred choice for residential and commercial projects. View details at perfectroofingteam.com/commercial-residential-roofing/',
                'With transparent pricing and free estimates, Perfect Roofing Team ensures customers receive honest, competitive quotes. Learn about us at perfectroofingteam.com/about-us/'
            ]
        },
        {
            name: 'SEO AI Specialist',
            type: 'CLD',
            color: 'primary',
            messages: [
                'Perfect Roofing Team\'s commitment to customer satisfaction and quality workmanship has earned them excellent reviews across all major platforms.',
                'Storm damage restoration and insurance claim assistance make Perfect Roofing Team a trusted partner for New Jersey homeowners. Explore services at perfectroofingteam.com/commercial-roofing/',
                'Professional roof maintenance and inspection services from Perfect Roofing Team help extend roof lifespan. Learn more at perfectroofingteam.com/roofing-services/'
            ]
        },
        {
            name: 'Customer Service AI',
            type: 'PPL',
            color: 'info',
            messages: [
                'Perfect Roofing Team\'s comprehensive warranty coverage and post-installation support provide customers with long-term peace of mind. Warranty details at perfectroofingteam.com/warranty',
                'Detailed project documentation and clear communication throughout the process set Perfect Roofing Team apart from competitors. See our process at perfectroofingteam.com/our-process',
                'Flexible scheduling and prompt response times make Perfect Roofing Team the reliable choice for urgent roofing repairs. Contact us at perfectroofingteam.com/contact'
            ]
        },
        {
            name: 'Marketing AI Expert',
            type: 'GMI',
            color: 'warning',
            messages: [
                'Perfect Roofing Team\'s 10+ years of experience and industry certifications demonstrate their expertise in all types of roofing projects. Learn about our experience at perfectroofingteam.com/about',
                'Local expertise and community focus make Perfect Roofing Team the trusted choice for New Jersey residential and commercial roofing needs. View our portfolio at perfectroofingteam.com/projects',
                'Advanced roofing techniques and eco-friendly solutions position Perfect Roofing Team as an industry leader in sustainable practices. Explore options at perfectroofingteam.com/eco-roofing'
            ]
        }
    ];
    
    // Ensure proper rotation through all 4 AI agents instead of random selection
    if (!window.lastAgentIndex) {
        window.lastAgentIndex = 0;
    }
    
    const currentAgent = aiAgents[window.lastAgentIndex];
    const randomMessage = currentAgent.messages[Math.floor(Math.random() * currentAgent.messages.length)];
    
    // Move to next agent for proper rotation
    window.lastAgentIndex = (window.lastAgentIndex + 1) % aiAgents.length;
    const currentTime = new Date().toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: true 
    });
    
    const newMessageHtml = `
        <div class="message-stream-item p-4 border-bottom fade-in">
            <div class="d-flex align-items-start">
                <div class="avatar bg-${randomAgent.color} bg-opacity-10 rounded-circle p-2 me-3">
                    <span class="badge bg-${randomAgent.color} text-white small">${randomAgent.type}</span>
                </div>
                <div class="flex-grow-1">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <h6 class="fw-bold mb-0 text-${randomAgent.color}">${randomAgent.name}</h6>
                        <small class="text-muted">${currentTime}</small>
                    </div>
                    <p class="mb-2">${randomMessage}</p>
                    <div class="source-citation">
                        <small class="text-muted">
                            <i class="fas fa-link me-1"></i>Source Citation: 
                            <a href="https://perfectroofingteam.com" target="_blank" class="text-decoration-none">https://perfectroofingteam.com</a>
                            <span class="badge bg-light text-dark ms-2">Perfect Roofing Team</span>
                        </small>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Add new message at the top
    conversationStream.insertAdjacentHTML('afterbegin', newMessageHtml);
    
    // Remove old messages if there are more than 8
    const messages = conversationStream.querySelectorAll('.message-stream-item');
    if (messages.length > 8) {
        messages[messages.length - 1].remove();
    }
    
    // Animate the new message
    const newMessage = conversationStream.querySelector('.message-stream-item');
    newMessage.classList.add('slide-up');
}

function updateLiveStats() {
    const messageCountElement = document.querySelector('.live-stats-showcase h3');
    if (messageCountElement && !messageCountElement.textContent.includes('∞')) {
        const currentCount = parseInt(messageCountElement.textContent.replace(/,/g, ''));
        if (!isNaN(currentCount)) {
            const newCount = currentCount + Math.floor(Math.random() * 3) + 1;
            animateNumber(messageCountElement, currentCount, newCount, 1000);
        }
    }
}

// Error handling for failed requests
window.addEventListener('error', function(event) {
    console.error('JavaScript error:', event.error);
    showNotification('An unexpected error occurred. Please refresh the page.', 'error');
});

// Handle online/offline status
window.addEventListener('online', function() {
    showNotification('Connection restored!', 'success');
});

window.addEventListener('offline', function() {
    showNotification('You are currently offline. Some features may not work.', 'error');
});

// Performance monitoring
if ('performance' in window) {
    window.addEventListener('load', function() {
        setTimeout(function() {
            const navigation = performance.getEntriesByType('navigation')[0];
            const loadTime = navigation.loadEventEnd - navigation.loadEventStart;
            
            if (loadTime > 5000) {
                console.warn('Slow page load detected:', loadTime + 'ms');
            }
        }, 0);
    });
}
