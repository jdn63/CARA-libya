/**
 * Libya CARA — Core JavaScript
 * Bilingual (Arabic/English) UI helpers
 */

'use strict';

(function () {

    // ── Risk color helpers ─────────────────────────────────────────────
    const RISK_COLORS = {
        critical:    '#8B0000',
        high:        '#CC3300',
        moderate:    '#FF8800',
        low:         '#FFD700',
        minimal:     '#336633',
        unavailable: '#adb5bd',
    };

    const RISK_LABELS_AR = {
        critical:    'بالغ الخطورة',
        high:        'مرتفع',
        moderate:    'متوسط',
        low:         'منخفض',
        minimal:     'ضئيل',
        unavailable: 'البيانات غير متاحة',
    };

    window.CARA = window.CARA || {};

    window.CARA.getRiskClass = function (level) {
        return 'risk-' + (level || 'unavailable');
    };

    window.CARA.getRiskColor = function (level) {
        return RISK_COLORS[level] || RISK_COLORS.unavailable;
    };

    window.CARA.getRiskLabelAr = function (level) {
        return RISK_LABELS_AR[level] || RISK_LABELS_AR.unavailable;
    };

    // ── Score → risk level mapping ────────────────────────────────────
    window.CARA.scoreToLevel = function (score) {
        if (score === null || score === undefined) return 'unavailable';
        score = parseFloat(score);
        if (isNaN(score)) return 'unavailable';
        if (score >= 0.75) return 'critical';
        if (score >= 0.55) return 'high';
        if (score >= 0.35) return 'moderate';
        if (score >= 0.15) return 'low';
        return 'minimal';
    };

    // ── Apply risk badge color from score ─────────────────────────────
    window.CARA.applyScoreBadge = function (element, score) {
        if (!element) return;
        const level = window.CARA.scoreToLevel(score);
        element.className = element.className.replace(/\brisk-\w+/g, '');
        element.classList.add('risk-score-badge', window.CARA.getRiskClass(level));
        if (score !== null && score !== undefined && !isNaN(parseFloat(score))) {
            element.textContent = (parseFloat(score) * 10).toFixed(1);
            element.title = window.CARA.getRiskLabelAr(level);
        } else {
            element.innerHTML = '<i class="fas fa-question"></i>';
            element.title = 'البيانات غير متاحة / Data not available';
        }
    };

    // ── Screen reader announcements ───────────────────────────────────
    window.CARA.announce = function (message) {
        var el = document.getElementById('sr-announcement');
        if (el) {
            el.textContent = '';
            setTimeout(function () { el.textContent = message; }, 50);
        }
    };

    // ── Low-connectivity cache helpers ────────────────────────────────
    window.CARA.cache = {
        set: function (key, data, ttlSeconds) {
            try {
                sessionStorage.setItem('cara_' + key, JSON.stringify({
                    data: data,
                    expires: Date.now() + (ttlSeconds || 3600) * 1000,
                }));
            } catch (e) { /* storage quota exceeded – silently ignore */ }
        },
        get: function (key) {
            try {
                var raw = sessionStorage.getItem('cara_' + key);
                if (!raw) return null;
                var obj = JSON.parse(raw);
                if (Date.now() > obj.expires) {
                    sessionStorage.removeItem('cara_' + key);
                    return null;
                }
                return obj.data;
            } catch (e) { return null; }
        },
    };

    // ── Municipality select: enable button on change ──────────────────
    document.addEventListener('DOMContentLoaded', function () {
        var sel = document.getElementById('municipality-select');
        var btn = document.getElementById('view-municipality-btn');

        if (sel && btn) {
            sel.addEventListener('change', function () {
                btn.disabled = !this.value;
            });
        }

        // Activate tooltips
        var tooltipEls = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltipEls.forEach(function (el) {
            new bootstrap.Tooltip(el);
        });
    });

})();
