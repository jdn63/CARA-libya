/**
 * CARA Platform Navigation Module
 * 
 * Handles jurisdiction selection, navigation between pages,
 * and navbar state management.
 */

import { StorageUtils, DomUtils } from './utils.js';

/**
 * Navigation Controller Class
 */
class NavigationController {
    constructor() {
        this.init();
    }

    /**
     * Initialize navigation functionality
     */
    init() {
        this.updateNavbarDisplay();
        this.setupEventListeners();
    }

    /**
     * Update navbar with selected jurisdiction
     */
    updateNavbarDisplay() {
        const jurisdiction = StorageUtils.getSelectedJurisdiction();
        const hercRegion = StorageUtils.getSelectedHercRegion();
        
        if (jurisdiction) {
            DomUtils.updateElementContent('jurisdiction-display', 
                jurisdiction.name);
        } else {
            DomUtils.updateElementContent('jurisdiction-display', '');
        }
    }

    /**
     * Handle jurisdiction selection
     * @param {string} jurisdictionId - Selected jurisdiction ID
     * @param {string} jurisdictionName - Selected jurisdiction name
     */
    selectJurisdiction(jurisdictionId, jurisdictionName) {
        if (!jurisdictionId) return;

        // Store selection
        StorageUtils.setSelectedJurisdiction(jurisdictionId, jurisdictionName);
        
        // Update navbar
        this.updateNavbarDisplay();
        
        // Navigate to dashboard
        window.location.href = `/dashboard/${jurisdictionId}`;
    }

    /**
     * Handle HERC region selection
     * @param {string} hercId - Selected HERC region ID
     * @param {string} hercName - Selected HERC region name
     */
    selectHercRegion(hercId, hercName) {
        if (!hercId) return;

        // Store selection
        StorageUtils.setSelectedHercRegion(hercId, hercName);
        
        // Navigate to HERC dashboard
        window.location.href = `/herc-dashboard/${hercId}`;
    }

    /**
     * Clear all selections (used on home page)
     */
    clearSelections() {
        StorageUtils.clearSelections();
        this.updateNavbarDisplay();
    }

    /**
     * Set up event listeners
     */
    setupEventListeners() {
        // Listen for page visibility changes to update navbar
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.updateNavbarDisplay();
            }
        });

        // Listen for storage changes from other tabs
        window.addEventListener('storage', (e) => {
            if (e.key && e.key.includes('selected')) {
                this.updateNavbarDisplay();
            }
        });
    }
}

/**
 * Modal Management for Regional Data
 */
export const ModalManager = {
    /**
     * Show HERC region statistics modal
     * @param {string} regionId - HERC region ID
     */
    async showHercStats(regionId) {
        try {
            // Remove existing modal if present
            const existingModal = document.getElementById('hercModal');
            if (existingModal) {
                existingModal.remove();
            }

            const data = await fetch(`/herc-data/${regionId}`).then(r => r.json());
            
            if (data.error) {
                console.error('HERC data error:', data.error);
                return;
            }

            const modalHtml = this.createHercModalHtml(regionId, data);
            document.body.insertAdjacentHTML('beforeend', modalHtml);
            
            const modal = new bootstrap.Modal(document.getElementById('hercModal'));
            modal.show();
        } catch (error) {
            console.error('Error loading HERC stats:', error);
        }
    },

    /**
     * Show WEM region statistics modal
     * @param {string} regionId - WEM region ID
     */
    async showWemStats(regionId) {
        try {
            // Remove existing modal if present
            const existingModal = document.getElementById('wemModal');
            if (existingModal) {
                existingModal.remove();
            }

            const data = await fetch(`/wem-data/${regionId}`).then(r => r.json());
            
            if (data.error) {
                console.error('WEM data error:', data.error);
                return;
            }

            const modalHtml = this.createWemModalHtml(regionId, data);
            document.body.insertAdjacentHTML('beforeend', modalHtml);
            
            const modal = new bootstrap.Modal(document.getElementById('wemModal'));
            modal.show();
        } catch (error) {
            console.error('Error loading WEM stats:', error);
        }
    },

    /**
     * Create HERC modal HTML
     * @param {string} regionId - HERC region ID
     * @param {Object} data - HERC region data
     * @returns {string} Modal HTML
     */
    createHercModalHtml(regionId, data) {
        return `
            <div class="modal fade" id="hercModal" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header bg-primary text-white">
                            <h5 class="modal-title">HERC Region ${regionId}</h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <h6>Health Preparedness Metrics</h6>
                                    <ul class="list-group mb-3">
                                        <li class="list-group-item d-flex justify-content-between align-items-center">
                                            Coalition Strength
                                            <span class="badge bg-primary rounded-pill">${data.metrics?.coalition_strength || 'N/A'}</span>
                                        </li>
                                        <li class="list-group-item d-flex justify-content-between align-items-center">
                                            Hospital Capacity
                                            <span class="badge bg-success rounded-pill">${data.metrics?.hospital_capacity || 'N/A'}</span>
                                        </li>
                                    </ul>
                                </div>
                                <div class="col-md-6">
                                    <h6>Member Organizations</h6>
                                    <ul class="list-group mb-3">
                                        <li class="list-group-item d-flex justify-content-between align-items-center">
                                            Health Departments
                                            <span class="badge bg-primary rounded-pill">${data.members?.health_departments || 0}</span>
                                        </li>
                                        <li class="list-group-item d-flex justify-content-between align-items-center">
                                            Hospitals
                                            <span class="badge bg-primary rounded-pill">${data.members?.hospitals || 0}</span>
                                        </li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>`;
    },

    /**
     * Create WEM modal HTML
     * @param {string} regionId - WEM region ID
     * @param {Object} data - WEM region data
     * @returns {string} Modal HTML
     */
    createWemModalHtml(regionId, data) {
        return `
            <div class="modal fade" id="wemModal" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header bg-danger text-white">
                            <h5 class="modal-title">WEM Region ${regionId}</h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <h6>Emergency Management Metrics</h6>
                                    <ul class="list-group mb-3">
                                        <li class="list-group-item d-flex justify-content-between align-items-center">
                                            Preparedness Score
                                            <span class="badge bg-${data.metrics?.preparedness_score > 0.7 ? 'success' : 'warning'} rounded-pill">
                                                ${((data.metrics?.preparedness_score || 0) * 100).toFixed(1)}%
                                            </span>
                                        </li>
                                        <li class="list-group-item d-flex justify-content-between align-items-center">
                                            Active Projects
                                            <span class="badge bg-primary rounded-pill">${data.metrics?.mitigation_projects || 0}</span>
                                        </li>
                                    </ul>
                                </div>
                                <div class="col-md-6">
                                    <h6>Resources</h6>
                                    <ul class="list-group mb-3">
                                        <li class="list-group-item d-flex justify-content-between align-items-center">
                                            Emergency Shelters
                                            <span class="badge bg-primary rounded-pill">${data.resources?.shelters || 0}</span>
                                        </li>
                                        <li class="list-group-item d-flex justify-content-between align-items-center">
                                            Response Units
                                            <span class="badge bg-primary rounded-pill">${data.resources?.response_units || 0}</span>
                                        </li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>`;
    },

    /**
     * Close modal by ID
     * @param {string} modalId - Modal element ID
     */
    closeModal(modalId) {
        const modalElement = document.getElementById(modalId);
        if (modalElement) {
            const modal = bootstrap.Modal.getInstance(modalElement);
            if (modal) {
                modal.hide();
            }
        }
    }
};

// Initialize navigation when DOM is ready
let navigationController;

document.addEventListener('DOMContentLoaded', () => {
    navigationController = new NavigationController();
    
    // Expose functions globally for legacy template compatibility
    window.selectJurisdiction = (id, name) => navigationController.selectJurisdiction(id, name);
    window.selectHercRegion = (id, name) => navigationController.selectHercRegion(id, name);
    window.showHercStats = (id) => ModalManager.showHercStats(id);
    window.showWemStats = (id) => ModalManager.showWemStats(id);
    window.closeHercStats = () => ModalManager.closeModal('hercModal');
    window.closeWemStats = () => ModalManager.closeModal('wemModal');
});

export default NavigationController;