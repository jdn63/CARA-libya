/**
 * CARA Platform Accessibility Module
 * 
 * Handles accessibility features including return-to-top functionality,
 * keyboard navigation, screen reader support, and WCAG compliance.
 */

import { DomUtils } from './utils.js';

/**
 * Accessibility Controller Class
 */
class AccessibilityController {
    constructor() {
        this.returnToTopButton = null;
        this.init();
    }

    /**
     * Initialize accessibility features
     */
    init() {
        this.setupReturnToTop();
        this.setupKeyboardNavigation();
        this.setupFocusManagement();
    }

    /**
     * Set up return-to-top button functionality
     */
    setupReturnToTop() {
        this.returnToTopButton = DomUtils.getElementById('return-to-top');
        
        if (!this.returnToTopButton) return;

        // Show/hide button based on scroll position
        window.addEventListener('scroll', () => {
            this.toggleReturnToTopButton();
        });

        // Handle button click
        DomUtils.addEventListenerSafe(this.returnToTopButton, 'click', (e) => {
            e.preventDefault();
            this.scrollToTop();
        });

        // Handle keyboard interaction
        DomUtils.addEventListenerSafe(this.returnToTopButton, 'keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.scrollToTop();
            }
        });
    }

    /**
     * Toggle return-to-top button visibility
     */
    toggleReturnToTopButton() {
        if (!this.returnToTopButton) return;

        const scrollThreshold = 200;
        const shouldShow = window.pageYOffset > scrollThreshold;

        if (shouldShow) {
            this.returnToTopButton.classList.remove('d-none');
            this.returnToTopButton.style.display = 'flex';
            this.returnToTopButton.style.alignItems = 'center';
            this.returnToTopButton.style.justifyContent = 'center';
        } else {
            this.returnToTopButton.classList.add('d-none');
            this.returnToTopButton.style.display = 'none';
        }
    }

    /**
     * Smooth scroll to top of page
     */
    scrollToTop() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });

        // Focus on main content for screen readers
        setTimeout(() => {
            const mainContent = document.querySelector('main') || document.querySelector('#main-content');
            if (mainContent) {
                mainContent.focus();
            }
        }, 500);
    }

    /**
     * Set up keyboard navigation enhancements
     */
    setupKeyboardNavigation() {
        // Skip link functionality
        const skipLink = document.querySelector('.skip-link');
        if (skipLink) {
            DomUtils.addEventListenerSafe(skipLink, 'click', (e) => {
                e.preventDefault();
                const target = document.querySelector(skipLink.getAttribute('href'));
                if (target) {
                    target.focus();
                    target.scrollIntoView({ behavior: 'smooth' });
                }
            });
        }

        // Enhanced keyboard navigation for modals
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeActiveModal();
            }
        });
    }

    /**
     * Set up focus management for dynamic content
     */
    setupFocusManagement() {
        // Focus management for dynamically loaded content
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'childList') {
                    mutation.addedNodes.forEach((node) => {
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            this.enhanceNewContent(node);
                        }
                    });
                }
            });
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    /**
     * Enhance newly added content for accessibility
     * @param {Element} element - New DOM element
     */
    enhanceNewContent(element) {
        // Add proper ARIA labels to buttons without them
        const buttons = element.querySelectorAll('button:not([aria-label]):not([aria-labelledby])');
        buttons.forEach(button => {
            if (!button.textContent.trim() && button.querySelector('i')) {
                // Button contains only an icon
                const iconClass = button.querySelector('i').className;
                if (iconClass.includes('fa-print')) {
                    button.setAttribute('aria-label', 'Print summary');
                } else if (iconClass.includes('fa-download')) {
                    button.setAttribute('aria-label', 'Download report');
                } else if (iconClass.includes('fa-close') || iconClass.includes('fa-times')) {
                    button.setAttribute('aria-label', 'Close');
                }
            }
        });

        // Ensure tables have proper headers
        const tables = element.querySelectorAll('table:not([role])');
        tables.forEach(table => {
            if (table.querySelector('thead th')) {
                table.setAttribute('role', 'table');
                const headerCells = table.querySelectorAll('thead th');
                headerCells.forEach((th, index) => {
                    if (!th.getAttribute('scope')) {
                        th.setAttribute('scope', 'col');
                    }
                });
            }
        });
    }

    /**
     * Close any active modal (for Escape key handling)
     */
    closeActiveModal() {
        const activeModal = document.querySelector('.modal.show');
        if (activeModal) {
            const modalInstance = bootstrap.Modal.getInstance(activeModal);
            if (modalInstance) {
                modalInstance.hide();
            }
        }
    }

    /**
     * Announce screen reader message
     * @param {string} message - Message to announce
     * @param {string} priority - 'polite' or 'assertive'
     */
    announceToScreenReader(message, priority = 'polite') {
        const announcement = document.createElement('div');
        announcement.setAttribute('aria-live', priority);
        announcement.setAttribute('aria-atomic', 'true');
        announcement.className = 'sr-only';
        announcement.textContent = message;
        
        document.body.appendChild(announcement);
        
        // Remove after announcement
        setTimeout(() => {
            document.body.removeChild(announcement);
        }, 1000);
    }
}

/**
 * High Contrast and Theme Management
 */
export const ThemeManager = {
    /**
     * Toggle high contrast mode
     */
    toggleHighContrast() {
        const html = document.documentElement;
        const isHighContrast = html.getAttribute('data-high-contrast') === 'true';
        
        html.setAttribute('data-high-contrast', !isHighContrast);
        localStorage.setItem('high-contrast', !isHighContrast);
        
        // Announce change to screen readers
        if (window.accessibilityController) {
            const message = isHighContrast ? 'High contrast disabled' : 'High contrast enabled';
            window.accessibilityController.announceToScreenReader(message);
        }
    },

    /**
     * Apply saved accessibility preferences
     */
    applySavedPreferences() {
        const highContrast = localStorage.getItem('high-contrast') === 'true';
        
        if (highContrast) {
            document.documentElement.setAttribute('data-high-contrast', 'true');
        }
    }
};

// Initialize accessibility when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Apply saved preferences first
    ThemeManager.applySavedPreferences();
    
    // Initialize accessibility controller
    window.accessibilityController = new AccessibilityController();
    
    // Expose theme functions globally
    window.toggleHighContrast = ThemeManager.toggleHighContrast;
});

export default AccessibilityController;