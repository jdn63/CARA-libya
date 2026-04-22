// Performance optimization utilities for all users
// This script permanently applies optimizations for better performance across all devices

/**
 * Core performance improvements that are always applied
 */
document.addEventListener('DOMContentLoaded', function() {
    // Apply core optimizations to any map on the page
    optimizeMaps();
    
    // Remove excessive transitions for better performance
    reduceAnimations();
    
    // Check connection and apply additional optimizations if needed
    if (detectSlowConnection()) {
        applyAdditionalOptimizations();
    }
    
    // Clean up any legacy settings
    cleanupLegacySettings();
});

/**
 * Optimize any maps on the page
 */
function optimizeMaps() {
    // Optimize any existing maps
    if (typeof L !== 'undefined' && window.riskMap) {
        // Apply performance-focused styling
        window.riskMap.eachLayer(function (layer) {
            if (layer.setStyle && typeof layer.setStyle === 'function') {
                layer.setStyle({
                    weight: 1,                 // Thinner borders
                    opacity: 0.8,              // Slightly transparent
                    fillOpacity: 0.6,          // Balanced fill opacity
                    renderer: L.canvas()       // Force canvas renderer
                });
            }
        });
        
        // Disable animations that consume CPU
        window.riskMap.options.zoomAnimation = false;
        window.riskMap.options.fadeAnimation = false;
        window.riskMap.options.markerZoomAnimation = false;
    }
}

/**
 * Reduce animations for better performance
 */
function reduceAnimations() {
    // Add a class that CSS can target to reduce animations
    document.body.classList.add('performance-optimized');
    
    // Add a media query that respects user preferences
    if (!document.getElementById('reduced-motion-style')) {
        const style = document.createElement('style');
        style.id = 'reduced-motion-style';
        style.innerHTML = `
            @media (prefers-reduced-motion: reduce) {
                *, *::before, *::after {
                    animation-duration: 0.001s !important;
                    transition-duration: 0.001s !important;
                }
            }
            
            .performance-optimized * {
                transition-duration: 0.2s !important;
                animation-duration: 0.2s !important;
            }
        `;
        document.head.appendChild(style);
    }
}

/**
 * Check for slow network conditions
 */
function detectSlowConnection() {
    if (navigator.connection) {
        // Network Information API is available
        const connection = navigator.connection;
        if (connection.effectiveType === 'slow-2g' || 
            connection.effectiveType === '2g' ||
            connection.saveData === true) {
            return true;
        }
    }
    
    return false;
}

/**
 * Apply additional optimizations for very slow connections
 */
function applyAdditionalOptimizations() {
    // Further reduce visual effects
    document.body.classList.add('extreme-performance-mode');
    
    // Disable any non-essential elements
    const nonEssentialElements = document.querySelectorAll('.non-essential');
    nonEssentialElements.forEach(el => {
        el.style.display = 'none';
    });
}

/**
 * Clean up any legacy settings from previous versions
 */
function cleanupLegacySettings() {
    // Clear any legacy localStorage items
    localStorage.removeItem('lightweightMode');
    localStorage.removeItem('performanceMode');
    
    // Remove any legacy CSS classes
    document.body.classList.remove('reduce-motion');
    document.body.classList.remove('reduce-effects');
}