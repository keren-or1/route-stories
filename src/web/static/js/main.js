/**
 * Route Stories - Main JavaScript
 * Handles form submission, AJAX calls, and UI interactions
 */

// ===== Utility Functions =====

/**
 * Show error message
 */
function showError(message, elementId = 'error-message') {
    const errorDiv = document.getElementById(elementId);
    if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
    }
}

/**
 * Hide error message
 */
function hideError(elementId = 'error-message') {
    const errorDiv = document.getElementById(elementId);
    if (errorDiv) {
        errorDiv.style.display = 'none';
    }
}

/**
 * Show loading state on button
 */
function setButtonLoading(buttonId, isLoading) {
    const button = document.getElementById(buttonId);
    if (!button) return;

    const btnText = button.querySelector('.btn-text');
    const btnLoader = button.querySelector('.btn-loader');

    if (isLoading) {
        button.disabled = true;
        if (btnText) btnText.style.display = 'none';
        if (btnLoader) btnLoader.style.display = 'flex';
    } else {
        button.disabled = false;
        if (btnText) btnText.style.display = 'inline';
        if (btnLoader) btnLoader.style.display = 'none';
    }
}

/**
 * Store route in local storage
 */
function storeRoute(routeId, data) {
    try {
        const routes = JSON.parse(localStorage.getItem('route-stories-routes') || '[]');
        routes.unshift({
            routeId: routeId,
            timestamp: new Date().toISOString(),
            origin: data.origin,
            destination: data.destination,
            totalWaypoints: data.total_waypoints
        });

        // Keep only last 10 routes
        if (routes.length > 10) {
            routes.pop();
        }

        localStorage.setItem('route-stories-routes', JSON.stringify(routes));
    } catch (error) {
        console.error('Error storing route:', error);
    }
}

/**
 * Get recent routes from local storage
 */
function getRecentRoutes() {
    try {
        return JSON.parse(localStorage.getItem('route-stories-routes') || '[]');
    } catch (error) {
        console.error('Error getting routes:', error);
        return [];
    }
}

// ===== Form Handling =====

/**
 * Initialize route form
 */
function initRouteForm() {
    const form = document.getElementById('route-form');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        hideError();

        // Get form data
        const startLocation = document.getElementById('start-location').value.trim();
        const endLocation = document.getElementById('end-location').value.trim();
        const maxPoints = document.getElementById('max-points').value;

        // Validate inputs
        if (!startLocation || !endLocation) {
            showError('Please enter both start and end locations');
            return;
        }

        // Show loading state
        setButtonLoading('submit-btn', true);

        try {
            // Submit route to backend
            const response = await fetch('/api/process-route', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    start: startLocation,
                    end: endLocation,
                    max_points: parseInt(maxPoints)
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to process route');
            }

            // Store route in local storage
            storeRoute(data.route_id, data);

            // Redirect to processing page
            window.location.href = `/processing/${data.route_id}`;

        } catch (error) {
            console.error('Error submitting route:', error);
            showError(error.message || 'An error occurred. Please try again.');
            setButtonLoading('submit-btn', false);
        }
    });
}

// ===== Notifications =====

/**
 * Show notification toast
 */
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;

    // Add styles
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        background: ${type === 'success' ? '#10B981' : type === 'error' ? '#EF4444' : '#4F46E5'};
        color: white;
        border-radius: 0.5rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        z-index: 1000;
        animation: slideIn 0.3s ease-out;
    `;

    // Add to DOM
    document.body.appendChild(notification);

    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Add notification animations to document
if (!document.getElementById('notification-styles')) {
    const style = document.createElement('style');
    style.id = 'notification-styles';
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        @keyframes slideOut {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
}

// ===== Copy to Clipboard =====

/**
 * Copy text to clipboard
 */
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showNotification('Copied to clipboard!', 'success');
    } catch (error) {
        console.error('Failed to copy:', error);
        showNotification('Failed to copy', 'error');
    }
}

// ===== Recent Routes =====

/**
 * Display recent routes on home page
 */
function displayRecentRoutes() {
    const container = document.getElementById('recent-routes');
    if (!container) return;

    const routes = getRecentRoutes();

    if (routes.length === 0) {
        container.innerHTML = '<p class="text-secondary">No recent routes</p>';
        return;
    }

    container.innerHTML = routes.map(route => `
        <div class="recent-route-item">
            <div class="route-details">
                <strong>${route.origin}</strong>
                <span>→</span>
                <strong>${route.destination}</strong>
            </div>
            <div class="route-meta">
                <span>${route.totalWaypoints} waypoints</span>
                <span>${new Date(route.timestamp).toLocaleDateString()}</span>
            </div>
            <a href="/results/${route.routeId}" class="btn btn-secondary btn-sm">
                View Results
            </a>
        </div>
    `).join('');
}

// ===== Input Validation =====

/**
 * Validate location input
 */
function validateLocation(input) {
    const value = input.value.trim();

    if (value.length === 0) {
        return { valid: false, message: 'This field is required' };
    }

    if (value.length < 2) {
        return { valid: false, message: 'Please enter a valid location' };
    }

    return { valid: true, message: '' };
}

/**
 * Add real-time validation to form inputs
 */
function initInputValidation() {
    const startInput = document.getElementById('start-location');
    const endInput = document.getElementById('end-location');

    if (startInput) {
        startInput.addEventListener('blur', function() {
            const validation = validateLocation(this);
            if (!validation.valid && this.value.length > 0) {
                this.style.borderColor = '#EF4444';
            } else {
                this.style.borderColor = '';
            }
        });
    }

    if (endInput) {
        endInput.addEventListener('blur', function() {
            const validation = validateLocation(this);
            if (!validation.valid && this.value.length > 0) {
                this.style.borderColor = '#EF4444';
            } else {
                this.style.borderColor = '';
            }
        });
    }
}

// ===== Accessibility =====

/**
 * Add keyboard navigation
 */
function initKeyboardNavigation() {
    document.addEventListener('keydown', (e) => {
        // Escape key to close modals or go back
        if (e.key === 'Escape') {
            const errorDiv = document.getElementById('error-message');
            if (errorDiv && errorDiv.style.display === 'block') {
                hideError();
            }
        }
    });
}

// ===== Analytics (Optional) =====

/**
 * Track route submission
 */
function trackRouteSubmission(routeId, origin, destination) {
    // Add analytics tracking here if needed
    console.log('Route submitted:', { routeId, origin, destination });
}

/**
 * Track page view
 */
function trackPageView(page) {
    // Add analytics tracking here if needed
    console.log('Page view:', page);
}

// ===== Initialization =====

/**
 * Initialize all components when DOM is ready
 */
document.addEventListener('DOMContentLoaded', () => {
    // Initialize form handling
    initRouteForm();

    // Initialize input validation
    initInputValidation();

    // Initialize keyboard navigation
    initKeyboardNavigation();

    // Display recent routes if container exists
    displayRecentRoutes();

    // Track page view
    const page = window.location.pathname;
    trackPageView(page);

    // Add smooth scroll behavior
    document.documentElement.style.scrollBehavior = 'smooth';

    console.log('Route Stories - Web UI Initialized');
});

// ===== Export functions for use in HTML =====
window.RouteStories = {
    showError,
    hideError,
    showNotification,
    copyToClipboard,
    getRecentRoutes,
    storeRoute
};
