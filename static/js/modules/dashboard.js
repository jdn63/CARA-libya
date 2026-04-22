import { StorageUtils, DomUtils } from './utils.js';

class DashboardController {
    constructor() {
        this.currentJurisdictionId = null;
        this.currentJurisdictionName = null;
        this.init();
    }

    init() {
        this.loadJurisdictionFromTemplate();
        this.updateJurisdictionData();
        this.setupEventListeners();
    }

    loadJurisdictionFromTemplate() {
        if (typeof window.templateData !== 'undefined') {
            this.currentJurisdictionId = window.templateData.jurisdictionId;
            this.currentJurisdictionName = window.templateData.jurisdictionName;
        }
    }

    updateJurisdictionData() {
        if (this.currentJurisdictionId && this.currentJurisdictionName) {
            StorageUtils.setSelectedJurisdiction(this.currentJurisdictionId, this.currentJurisdictionName);
            DomUtils.updateElementContent('jurisdiction-display', 
                this.currentJurisdictionName);
        }
    }

    setupEventListeners() {
        const printButtons = document.querySelectorAll('[href*="/print-summary/"]');
        printButtons.forEach(button => {
            DomUtils.addEventListenerSafe(button, 'click', (e) => {
                this.trackAction('print_summary');
            });
        });

        const actionButtons = document.querySelectorAll('[href*="/action-plan/"]');
        actionButtons.forEach(button => {
            DomUtils.addEventListenerSafe(button, 'click', (e) => {
                this.trackAction('generate_action_plan');
            });
        });
    }

    trackAction(action) {
        console.log(`Dashboard action: ${action}`, {
            jurisdiction: this.currentJurisdictionName,
            timestamp: new Date().toISOString()
        });
    }

    destroy() {
    }
}

let dashboardController;

document.addEventListener('DOMContentLoaded', () => {
    dashboardController = new DashboardController();
    window.dashboardController = dashboardController;
});

window.addEventListener('beforeunload', () => {
    if (dashboardController) {
        dashboardController.destroy();
    }
});

export default DashboardController;
