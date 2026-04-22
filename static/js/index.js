document.addEventListener('DOMContentLoaded', function() {
    console.log("Main.js loaded - generic version");
    console.log("Main.js loaded - static map version");
    
    // Clear any previously selected items when landing on the home page
    // This ensures a fresh start when users open a new browser session
    localStorage.removeItem('selectedJurisdictionId');
    localStorage.removeItem('selectedJurisdictionName');
    localStorage.removeItem('selectedHercId');
    localStorage.removeItem('selectedHercName');
    
    // Update the display in the navbar
    const jurisdictionDisplay = document.getElementById('jurisdiction-display');
    if (jurisdictionDisplay) {
        jurisdictionDisplay.innerHTML = '';
    }
    
    // No longer initializing interactive map - using static image instead
    
    // Jurisdiction selection functionality
    function selectJurisdiction(jurisdictionId, jurisdictionName) {
        if (jurisdictionId) {
            // Store the selected jurisdiction in localStorage
            localStorage.setItem('selectedJurisdictionId', jurisdictionId);
            localStorage.setItem('selectedJurisdictionName', jurisdictionName);
            
            // Navigate to the dashboard
            window.location.href = `/dashboard/${jurisdictionId}`;
        }
    }
    
    // HERC region selection functionality
    function selectHercRegion(hercId, hercName) {
        if (hercId) {
            // Store the selected HERC region in localStorage
            localStorage.setItem('selectedHercId', hercId);
            localStorage.setItem('selectedHercName', hercName);
            
            // Navigate to the HERC dashboard
            window.location.href = `/herc-dashboard/${hercId}`;
        }
    }
    
    // Make selection functions available globally
    window.selectJurisdiction = selectJurisdiction;
    window.selectHercRegion = selectHercRegion;
    
    // Utility functions for risk levels (needed for any risk data display)
    function getRiskLevel(score) {
        if (score < 0.3) return 'Low';
        if (score < 0.6) return 'Medium';
        return 'High';
    }

    function getRiskColor(level) {
        switch (level) {
            case 'Low': return 'success';
            case 'Medium': return 'warning';
            case 'High': return 'danger';
            default: return 'secondary';
        }
    }

    function getColorForRisk(score) {
        return score > 0.6 ? '#dc3545' :  // High risk - red
               score > 0.3 ? '#ffc107' :  // Medium risk - yellow
                            '#28a745';    // Low risk - green
    }
});