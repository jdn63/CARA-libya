// JavaScript for accessibility features

document.addEventListener('DOMContentLoaded', function() {
    // Initialize accessibility settings
    initAccessibilityMode();
    
    // Set up event listener for the accessibility toggle button
    const accessibilityToggle = document.getElementById('accessibility-toggle');
    
    if (accessibilityToggle) {
        accessibilityToggle.addEventListener('click', function() {
            toggleAccessibilityMode();
        });
        
        // Also allow keyboard toggle with Enter or Space key
        accessibilityToggle.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                toggleAccessibilityMode();
            }
        });
    }
    
    // Add keyboard navigation for all interactive elements
    improveKeyboardNavigation();
});

// Initialize accessibility mode based on stored preference
function initAccessibilityMode() {
    // Check if high contrast mode was previously enabled
    const highContrastEnabled = localStorage.getItem('highContrastMode') === 'true';
    
    // Set initial state
    document.documentElement.setAttribute('data-high-contrast', highContrastEnabled);
    
    // Update toggle button appearance if it exists
    updateToggleButton(highContrastEnabled);
    
    // Announce to screen readers if high contrast is active
    if (highContrastEnabled) {
        announceToScreenReader('High contrast mode is active');
    }
}

// Toggle accessibility mode on/off
function toggleAccessibilityMode() {
    // Get current state
    const currentState = document.documentElement.getAttribute('data-high-contrast') === 'true';
    
    // Toggle to opposite state
    const newState = !currentState;
    
    // Save preference
    localStorage.setItem('highContrastMode', newState);
    
    // Apply new state
    document.documentElement.setAttribute('data-high-contrast', newState);
    
    // Update toggle button appearance
    updateToggleButton(newState);
    
    // Announce change to screen readers
    if (newState) {
        announceToScreenReader('High contrast mode enabled');
    } else {
        announceToScreenReader('High contrast mode disabled');
    }
}

// Update the toggle button appearance
function updateToggleButton(highContrastEnabled) {
    const toggleButton = document.getElementById('accessibility-toggle');
    const toggleIcon = document.getElementById('accessibility-icon');
    const toggleText = document.getElementById('accessibility-text');
    
    if (toggleButton && toggleIcon && toggleText) {
        if (highContrastEnabled) {
            toggleIcon.className = 'fas fa-eye';
            toggleText.textContent = 'Standard Display';
            toggleButton.setAttribute('aria-pressed', 'true');
        } else {
            toggleIcon.className = 'fas fa-eye';
            toggleText.textContent = 'High Contrast';
            toggleButton.setAttribute('aria-pressed', 'false');
        }
    }
}

// Announce messages to screen readers using aria-live region
function announceToScreenReader(message) {
    let announcement = document.getElementById('screen-reader-announcement');
    
    // Create the announcement element if it doesn't exist
    if (!announcement) {
        announcement = document.createElement('div');
        announcement.id = 'screen-reader-announcement';
        announcement.className = 'sr-only';
        announcement.setAttribute('aria-live', 'polite');
        announcement.setAttribute('aria-atomic', 'true');
        document.body.appendChild(announcement);
    }
    
    // Set the message
    announcement.textContent = message;
    
    // Clear after 3 seconds to avoid cluttering screen reader output
    setTimeout(() => {
        announcement.textContent = '';
    }, 3000);
}

// Improve keyboard navigation for all interactive elements
function improveKeyboardNavigation() {
    // Ensure all interactive elements are keyboard accessible
    
    // Add tabindex to elements that might be missing it
    const potentiallyInteractiveElements = document.querySelectorAll('.card, .alert, [role="button"]');
    potentiallyInteractiveElements.forEach(el => {
        if (!el.getAttribute('tabindex')) {
            el.setAttribute('tabindex', '0');
        }
    });
    
    // Ensure buttons without types have proper type
    const buttons = document.querySelectorAll('button:not([type])');
    buttons.forEach(button => {
        button.setAttribute('type', 'button');
    });
    
    // Improve skip navigation
    addSkipToMainContentLink();
}

// Add a skip to main content link for keyboard users
function addSkipToMainContentLink() {
    // Check if it already exists
    if (document.getElementById('skip-to-main-content')) {
        return;
    }
    
    const skipLink = document.createElement('a');
    skipLink.id = 'skip-to-main-content';
    skipLink.href = '#main-content';
    skipLink.className = 'sr-only sr-only-focusable';
    skipLink.textContent = 'Skip to main content';
    
    // Style for when it receives focus
    skipLink.style.cssText = `
        position: absolute;
        padding: 10px;
        background: #0050ff;
        color: white;
        top: 0;
        left: 0;
        z-index: 1100;
        text-decoration: none;
        font-weight: bold;
    `;
    
    // Add the link as the first element in the body
    document.body.insertBefore(skipLink, document.body.firstChild);
    
    // Add id to main content for the link to work
    const mainContent = document.querySelector('main');
    if (mainContent && !mainContent.id) {
        mainContent.id = 'main-content';
    }
}