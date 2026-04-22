/**
 * Legacy Navigation Functions
 * 
 * These functions provide backward compatibility for templates
 * that still use the old navigation approach.
 */

// Functions to navigate to jurisdiction-specific pages
function goToDashboard() {
    const jurisdictionId = localStorage.getItem('selectedJurisdictionId');
    if (jurisdictionId) {
        window.location.href = `/dashboard/${jurisdictionId}`;
    } else {
        alert('Please select a jurisdiction from the home page first.');
        window.location.href = '/';
    }
}

function goToActionPlan() {
    const jurisdictionId = localStorage.getItem('selectedJurisdictionId');
    if (jurisdictionId) {
        window.location.href = `/action-plan/${jurisdictionId}`;
    } else {
        alert('Please select a jurisdiction from the home page first.');
        window.location.href = '/';
    }
}

function goToPrintSummary() {
    const jurisdictionId = localStorage.getItem('selectedJurisdictionId');
    if (jurisdictionId) {
        window.location.href = `/print-summary/${jurisdictionId}`;
    } else {
        alert('Please select a jurisdiction from the home page first.');
        window.location.href = '/';
    }
}

// Export functions for modern modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        goToDashboard,
        goToActionPlan,
        goToPrintSummary
    };
}

// Make functions available globally for legacy templates
window.goToDashboard = goToDashboard;
window.goToActionPlan = goToActionPlan;
window.goToPrintSummary = goToPrintSummary;