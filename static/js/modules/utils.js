/**
 * CARA Platform Utilities Module
 * 
 * Core utility functions for risk calculations, data formatting,
 * and common operations across the platform.
 */

/**
 * Risk Level Utilities
 */
export const RiskUtils = {
    /**
     * Convert numeric risk score to descriptive level
     * @param {number} score - Risk score (0.0 - 1.0)
     * @returns {string} Risk level description
     */
    getRiskLevel(score) {
        if (score < 0.3) return 'Low';
        if (score < 0.6) return 'Medium';
        return 'High';
    },

    /**
     * Get Bootstrap color class for risk level
     * @param {string} level - Risk level ('Low', 'Medium', 'High')
     * @returns {string} Bootstrap color class
     */
    getRiskColor(level) {
        switch (level) {
            case 'Low': return 'success';
            case 'Medium': return 'warning';
            case 'High': return 'danger';
            default: return 'secondary';
        }
    },

    /**
     * Get hex color for risk score visualization
     * @param {number} score - Risk score (0.0 - 1.0)
     * @returns {string} Hex color code
     */
    getColorForRisk(score) {
        return score > 0.6 ? '#dc3545' :  // High risk - red
               score > 0.3 ? '#ffc107' :  // Medium risk - yellow
                            '#28a745';    // Low risk - green
    },

    /**
     * Format risk score as percentage
     * @param {number} score - Risk score (0.0 - 1.0)
     * @param {number} decimals - Number of decimal places
     * @returns {string} Formatted percentage
     */
    formatAsPercentage(score, decimals = 1) {
        return (score * 100).toFixed(decimals) + '%';
    }
};

/**
 * Data Storage Utilities
 */
export const StorageUtils = {
    /**
     * Store jurisdiction selection in localStorage
     * @param {string} id - Jurisdiction ID
     * @param {string} name - Jurisdiction name
     */
    setSelectedJurisdiction(id, name) {
        localStorage.setItem('selectedJurisdictionId', id);
        localStorage.setItem('selectedJurisdictionName', name);
    },

    /**
     * Get selected jurisdiction from localStorage
     * @returns {Object} Jurisdiction data or null
     */
    getSelectedJurisdiction() {
        const id = localStorage.getItem('selectedJurisdictionId');
        const name = localStorage.getItem('selectedJurisdictionName');
        return id && name ? { id, name } : null;
    },

    /**
     * Store HERC region selection in localStorage
     * @param {string} id - HERC region ID
     * @param {string} name - HERC region name
     */
    setSelectedHercRegion(id, name) {
        localStorage.setItem('selectedHercId', id);
        localStorage.setItem('selectedHercName', name);
    },

    /**
     * Get selected HERC region from localStorage
     * @returns {Object} HERC region data or null
     */
    getSelectedHercRegion() {
        const id = localStorage.getItem('selectedHercId');
        const name = localStorage.getItem('selectedHercName');
        return id && name ? { id, name } : null;
    },

    /**
     * Clear all stored selections
     */
    clearSelections() {
        localStorage.removeItem('selectedJurisdictionId');
        localStorage.removeItem('selectedJurisdictionName');
        localStorage.removeItem('selectedHercId');
        localStorage.removeItem('selectedHercName');
    }
};

/**
 * API Request Utilities
 */
export const ApiUtils = {
    /**
     * Make authenticated API request
     * @param {string} url - API endpoint
     * @param {Object} options - Fetch options
     * @returns {Promise} Response data
     */
    async fetchWithRetry(url, options = {}) {
        const maxRetries = 3;
        let lastError;

        for (let i = 0; i < maxRetries; i++) {
            try {
                const response = await fetch(url, {
                    headers: {
                        'Content-Type': 'application/json',
                        ...options.headers
                    },
                    ...options
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                return await response.json();
            } catch (error) {
                lastError = error;
                if (i < maxRetries - 1) {
                    await this.delay(1000 * (i + 1)); // Exponential backoff
                }
            }
        }

        throw lastError;
    },

    /**
     * Utility delay function
     * @param {number} ms - Milliseconds to delay
     * @returns {Promise}
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
};

/**
 * DOM Utilities
 */
export const DomUtils = {
    /**
     * Safely get element by ID
     * @param {string} id - Element ID
     * @returns {Element|null}
     */
    getElementById(id) {
        return document.getElementById(id);
    },

    /**
     * Update element content safely
     * @param {string} id - Element ID
     * @param {string} content - HTML content
     */
    updateElementContent(id, content) {
        const element = this.getElementById(id);
        if (element) {
            element.innerHTML = content;
        }
    },

    /**
     * Add event listener with error handling
     * @param {Element} element - DOM element
     * @param {string} event - Event type
     * @param {Function} handler - Event handler
     */
    addEventListenerSafe(element, event, handler) {
        if (element && typeof handler === 'function') {
            element.addEventListener(event, (e) => {
                try {
                    handler(e);
                } catch (error) {
                    console.error(`Error in ${event} handler:`, error);
                }
            });
        }
    }
};

/**
 * Export all utilities as default
 */
export default {
    RiskUtils,
    StorageUtils,
    ApiUtils,
    DomUtils
};