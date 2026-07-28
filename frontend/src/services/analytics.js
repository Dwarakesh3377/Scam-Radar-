// Analytics Service for ScamRadar
import { api } from './api';

class AnalyticsService {
    constructor() {
        this.sessionId = this.generateSessionId();
        this.userId = null;
        this.analyticsQueue = [];
        this.isSending = false;
        this.flushInterval = 30000; // 30 seconds
        this.maxQueueSize = 100;
        
        // Start flush interval
        this.startFlushInterval();
        
        // Track page view on initialization
        this.trackPageView();
        
        // Setup beforeunload to send remaining analytics
        window.addEventListener('beforeunload', () => {
            this.flushAnalytics();
        });
    }
    
    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    setUser(userId) {
        this.userId = userId;
        this.trackUserEvent('user_login', { userId });
    }
    
    clearUser() {
        this.trackUserEvent('user_logout', { userId: this.userId });
        this.userId = null;
    }
    
    startFlushInterval() {
        setInterval(() => {
            this.flushAnalytics();
        }, this.flushInterval);
    }
    
    async flushAnalytics() {
        if (this.isSending || this.analyticsQueue.length === 0) {
            return;
        }
        
        this.isSending = true;
        
        try {
            // Create a copy of the queue and clear it
            const queueToSend = [...this.analyticsQueue];
            this.analyticsQueue = [];
            
            // Send analytics data to server
            await api.post('/analytics/batch', {
                events: queueToSend,
                sessionId: this.sessionId,
                userId: this.userId,
                timestamp: new Date().toISOString()
            });
            
            console.log(`Analytics flushed: ${queueToSend.length} events sent`);
        } catch (error) {
            console.error('Failed to send analytics:', error);
            // Restore queue on error
            this.analyticsQueue = [...this.analyticsQueue, ...queueToSend];
        } finally {
            this.isSending = false;
        }
    }
    
    trackEvent(eventType, eventData = {}) {
        const event = {
            type: eventType,
            data: eventData,
            timestamp: new Date().toISOString(),
            sessionId: this.sessionId,
            userId: this.userId,
            page: window.location.pathname,
            userAgent: navigator.userAgent,
            screenResolution: `${window.screen.width}x${window.screen.height}`,
            language: navigator.language
        };
        
        // Add to queue
        this.analyticsQueue.push(event);
        
        // If queue is too large, flush immediately
        if (this.analyticsQueue.length >= this.maxQueueSize) {
            this.flushAnalytics();
        }
        
        // Also log to console in development
        if (import.meta.env.DEV) {
            console.log(`Analytics Event: ${eventType}`, eventData);
        }
        
        return event;
    }
    
    // Page Tracking
    trackPageView(pageData = {}) {
        return this.trackEvent('page_view', {
            page: window.location.pathname,
            referrer: document.referrer,
            ...pageData
        });
    }
    
    trackPageExit(pageData = {}) {
        return this.trackEvent('page_exit', {
            page: window.location.pathname,
            timeOnPage: this.getTimeOnPage(),
            ...pageData
        });
    }
    
    // User Events
    trackUserEvent(action, data = {}) {
        return this.trackEvent('user_action', {
            action,
            userId: this.userId,
            ...data
        });
    }
    
    trackLogin(method, data = {}) {
        return this.trackEvent('user_login', {
            method,
            timestamp: new Date().toISOString(),
            ...data
        });
    }
    
    trackLogout() {
        return this.trackEvent('user_logout', {
            userId: this.userId,
            timestamp: new Date().toISOString()
        });
    }
    
    trackSignup(method, data = {}) {
        return this.trackEvent('user_signup', {
            method,
            timestamp: new Date().toISOString(),
            ...data
        });
    }
    
    // Analysis Events
    trackAnalysisStart(inputType, metadata = {}) {
        return this.trackEvent('analysis_start', {
            inputType,
            metadata,
            timestamp: new Date().toISOString()
        });
    }
    
    trackAnalysisComplete(result, metadata = {}) {
        return this.trackEvent('analysis_complete', {
            result: {
                score: result.score,
                category: result.category,
                confidence: result.confidence,
                riskLevel: result.riskLevel
            },
            metadata,
            timestamp: new Date().toISOString(),
            analysisTime: this.getAnalysisTime()
        });
    }
    
    trackAnalysisError(error, inputType, metadata = {}) {
        return this.trackEvent('analysis_error', {
            error: error.message || 'Unknown error',
            inputType,
            metadata,
            timestamp: new Date().toISOString()
        });
    }
    
    // Feedback Events
    trackFeedback(submission, analysisId = null) {
        return this.trackEvent('feedback_submitted', {
            rating: submission.rating,
            commentLength: submission.comment?.length || 0,
            analysisId,
            timestamp: new Date().toISOString()
        });
    }
    
    trackReview(review, companyName) {
        return this.trackEvent('review_submitted', {
            companyName,
            scamType: review.scamType,
            lossAmount: review.lossAmount,
            country: review.country,
            timestamp: new Date().toISOString()
        });
    }
    
    // UI Interactions
    trackButtonClick(buttonId, page, data = {}) {
        return this.trackEvent('button_click', {
            buttonId,
            page,
            ...data
        });
    }
    
    trackLinkClick(linkId, destination, page) {
        return this.trackEvent('link_click', {
            linkId,
            destination,
            page
        });
    }
    
    trackFormSubmit(formId, fieldCount, page) {
        return this.trackEvent('form_submit', {
            formId,
            fieldCount,
            page
        });
    }
    
    trackFormFieldInteraction(fieldId, action, formId, page) {
        return this.trackEvent('form_field_interaction', {
            fieldId,
            action,
            formId,
            page
        });
    }
    
    // Search and Filter Events
    trackSearch(query, resultsCount, searchType) {
        return this.trackEvent('search_performed', {
            query,
            resultsCount,
            searchType,
            timestamp: new Date().toISOString()
        });
    }
    
    trackFilterApplied(filterType, filterValue, resultsCount) {
        return this.trackEvent('filter_applied', {
            filterType,
            filterValue,
            resultsCount,
            timestamp: new Date().toISOString()
        });
    }
    
    trackSortApplied(sortBy, sortOrder, resultsCount) {
        return this.trackEvent('sort_applied', {
            sortBy,
            sortOrder,
            resultsCount,
            timestamp: new Date().toISOString()
        });
    }
    
    // Export Events
    trackExport(format, dataType, itemCount) {
        return this.trackEvent('export_performed', {
            format,
            dataType,
            itemCount,
            timestamp: new Date().toISOString()
        });
    }
    
    // Error Tracking
    trackError(error, context = {}) {
        return this.trackEvent('error_occurred', {
            error: error.message || 'Unknown error',
            stack: error.stack,
            context,
            timestamp: new Date().toISOString(),
            page: window.location.pathname
        });
    }
    
    // Performance Tracking
    trackPerformance(metric, value, metadata = {}) {
        return this.trackEvent('performance_metric', {
            metric,
            value,
            metadata,
            timestamp: new Date().toISOString()
        });
    }
    
    trackPageLoadTime(loadTime, page) {
        return this.trackPerformance('page_load_time', loadTime, { page });
    }
    
    trackApiCall(apiEndpoint, method, duration, statusCode) {
        return this.trackPerformance('api_call', duration, {
            endpoint: apiEndpoint,
            method,
            statusCode
        });
    }
    
    // Social Sharing
    trackShare(platform, contentType, contentId) {
        return this.trackEvent('content_shared', {
            platform,
            contentType,
            contentId,
            timestamp: new Date().toISOString()
        });
    }
    
    // Theme and Settings
    trackThemeChange(theme) {
        return this.trackEvent('theme_changed', {
            theme,
            timestamp: new Date().toISOString()
        });
    }
    
    trackLanguageChange(language) {
        return this.trackEvent('language_changed', {
            language,
            timestamp: new Date().toISOString()
        });
    }
    
    trackSettingsChange(setting, value) {
        return this.trackEvent('settings_changed', {
            setting,
            value,
            timestamp: new Date().toISOString()
        });
    }
    
    // Helper Methods
    getTimeOnPage() {
        if (!this.pageStartTime) {
            this.pageStartTime = Date.now();
            return 0;
        }
        return Date.now() - this.pageStartTime;
    }
    
    getAnalysisTime() {
        if (!this.analysisStartTime) {
            this.analysisStartTime = Date.now();
            return 0;
        }
        return Date.now() - this.analysisStartTime;
    }
    
    resetPageTimer() {
        this.pageStartTime = Date.now();
    }
    
    resetAnalysisTimer() {
        this.analysisStartTime = Date.now();
    }
    
    // Analytics Data Retrieval
    async getAnalyticsSummary(timeRange = 'day') {
        try {
            const response = await api.get('/analytics/summary', {
                params: { timeRange }
            });
            return response.data;
        } catch (error) {
            console.error('Failed to get analytics summary:', error);
            throw error;
        }
    }
    
    async getUserAnalytics(userId, timeRange = 'day') {
        try {
            const response = await api.get(`/analytics/user/${userId}`, {
                params: { timeRange }
            });
            return response.data;
        } catch (error) {
            console.error('Failed to get user analytics:', error);
            throw error;
        }
    }
    
    async getAnalysisTrends(timeRange = 'week', interval = 'day') {
        try {
            const response = await api.get('/analytics/trends', {
                params: { timeRange, interval }
            });
            return response.data;
        } catch (error) {
            console.error('Failed to get analysis trends:', error);
            throw error;
        }
    }
    
    async getRiskDistribution(timeRange = 'month') {
        try {
            const response = await api.get('/analytics/risk-distribution', {
                params: { timeRange }
            });
            return response.data;
        } catch (error) {
            console.error('Failed to get risk distribution:', error);
            throw error;
        }
    }
    
    async getTopScamCompanies(limit = 10, timeRange = 'month') {
        try {
            const response = await api.get('/analytics/top-scams', {
                params: { limit, timeRange }
            });
            return response.data;
        } catch (error) {
            console.error('Failed to get top scam companies:', error);
            throw error;
        }
    }
    
    async getUserActivity(userId, limit = 50) {
        try {
            const response = await api.get(`/analytics/user/${userId}/activity`, {
                params: { limit }
            });
            return response.data;
        } catch (error) {
            console.error('Failed to get user activity:', error);
            throw error;
        }
    }
    
    async getPopularSearches(limit = 10, timeRange = 'week') {
        try {
            const response = await api.get('/analytics/popular-searches', {
                params: { limit, timeRange }
            });
            return response.data;
        } catch (error) {
            console.error('Failed to get popular searches:', error);
            throw error;
        }
    }
    
    async getConversionRate(timeRange = 'month') {
        try {
            const response = await api.get('/analytics/conversion-rate', {
                params: { timeRange }
            });
            return response.data;
        } catch (error) {
            console.error('Failed to get conversion rate:', error);
            throw error;
        }
    }
    
    async getRetentionRate(timeRange = 'month') {
        try {
            const response = await api.get('/analytics/retention-rate', {
                params: { timeRange }
            });
            return response.data;
        } catch (error) {
            console.error('Failed to get retention rate:', error);
            throw error;
        }
    }
    
    // Real-time Analytics
    async getRealTimeStats() {
        try {
            const response = await api.get('/analytics/realtime');
            return response.data;
        } catch (error) {
            console.error('Failed to get real-time stats:', error);
            throw error;
        }
    }
    
    async getActiveUsers() {
        try {
            const response = await api.get('/analytics/active-users');
            return response.data;
        } catch (error) {
            console.error('Failed to get active users:', error);
            throw error;
        }
    }
    
    // Export Analytics Data
    async exportAnalyticsData(format = 'csv', filters = {}) {
        try {
            const response = await api.get(`/analytics/export/${format}`, {
                params: filters,
                responseType: 'blob'
            });
            
            // Create download link
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            
            // Generate filename with timestamp
            const timestamp = new Date().toISOString().split('T')[0];
            link.setAttribute('download', `scamradar-analytics-${timestamp}.${format}`);
            
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(url);
            
            return true;
        } catch (error) {
            console.error('Failed to export analytics data:', error);
            throw error;
        }
    }
    
    // Health Check
    async checkAnalyticsHealth() {
        try {
            const response = await api.get('/analytics/health');
            return response.data;
        } catch (error) {
            console.error('Analytics health check failed:', error);
            return { status: 'unhealthy', error: error.message };
        }
    }
    
    // Privacy Controls
    clearUserAnalytics(userId) {
        return this.trackEvent('analytics_cleared', {
            userId,
            timestamp: new Date().toISOString()
        });
    }
    
    optOut() {
        this.analyticsQueue = [];
        this.isSending = false;
        localStorage.setItem('analytics_opt_out', 'true');
        return this.trackEvent('analytics_opt_out', {
            timestamp: new Date().toISOString()
        });
    }
    
    optIn() {
        localStorage.removeItem('analytics_opt_out');
        return this.trackEvent('analytics_opt_in', {
            timestamp: new Date().toISOString()
        });
    }
    
    isOptedOut() {
        return localStorage.getItem('analytics_opt_out') === 'true';
    }
    
    // Debug Methods
    getQueueSize() {
        return this.analyticsQueue.length;
    }
    
    getSessionId() {
        return this.sessionId;
    }
    
    clearQueue() {
        this.analyticsQueue = [];
    }
    
    // Event Listeners Setup
    setupEventListeners() {
        // Track all button clicks
        document.addEventListener('click', (event) => {
            const button = event.target.closest('button, [role="button"]');
            if (button) {
                const buttonId = button.id || button.getAttribute('data-testid') || button.textContent.trim();
                const page = window.location.pathname;
                this.trackButtonClick(buttonId, page);
            }
        });
        
        // Track form submissions
        document.addEventListener('submit', (event) => {
            const form = event.target;
            const formId = form.id || 'unknown_form';
            const fieldCount = form.querySelectorAll('input, select, textarea').length;
            const page = window.location.pathname;
            this.trackFormSubmit(formId, fieldCount, page);
        });
        
        // Track link clicks
        document.addEventListener('click', (event) => {
            const link = event.target.closest('a');
            if (link && link.href) {
                const linkId = link.id || link.textContent.trim();
                const destination = link.href;
                const page = window.location.pathname;
                this.trackLinkClick(linkId, destination, page);
            }
        });
        
        // Track form field interactions
        document.addEventListener('focus', (event) => {
            const field = event.target;
            if (field.matches('input, select, textarea')) {
                const fieldId = field.id || field.name || 'unknown_field';
                const form = field.closest('form');
                const formId = form ? (form.id || 'unknown_form') : 'no_form';
                const page = window.location.pathname;
                this.trackFormFieldInteraction(fieldId, 'focus', formId, page);
            }
        }, true);
        
        document.addEventListener('blur', (event) => {
            const field = event.target;
            if (field.matches('input, select, textarea')) {
                const fieldId = field.id || field.name || 'unknown_field';
                const form = field.closest('form');
                const formId = form ? (form.id || 'unknown_form') : 'no_form';
                const page = window.location.pathname;
                this.trackFormFieldInteraction(fieldId, 'blur', formId, page);
            }
        }, true);
        
        // Track errors
        window.addEventListener('error', (event) => {
            this.trackError(new Error(event.message), {
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno
            });
        });
        
        // Track unhandled promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            this.trackError(event.reason, {
                type: 'unhandled_promise_rejection'
            });
        });
        
        // Track page performance
        if ('performance' in window) {
            window.addEventListener('load', () => {
                const loadTime = performance.timing.loadEventEnd - performance.timing.navigationStart;
                this.trackPageLoadTime(loadTime, window.location.pathname);
                
                // Track individual performance metrics
                const metrics = {
                    dns: performance.timing.domainLookupEnd - performance.timing.domainLookupStart,
                    tcp: performance.timing.connectEnd - performance.timing.connectStart,
                    request: performance.timing.responseStart - performance.timing.requestStart,
                    response: performance.timing.responseEnd - performance.timing.responseStart,
                    dom: performance.timing.domContentLoadedEventEnd - performance.timing.domLoading,
                    load: performance.timing.loadEventEnd - performance.timing.loadEventStart
                };
                
                Object.entries(metrics).forEach(([metric, value]) => {
                    this.trackPerformance(`page_${metric}_time`, value);
                });
            });
        }
    }
    
    // Initialize the service
    initialize() {
        if (this.isOptedOut()) {
            console.log('Analytics opted out');
            return;
        }
        
        this.setupEventListeners();
        
        // Track initial page view
        this.trackPageView();
        
        console.log('Analytics service initialized');
    }
}

// Create singleton instance
const analyticsService = new AnalyticsService();

// Export the service
export default analyticsService;

// Also export individual methods for convenience
export const trackEvent = (eventType, eventData) => analyticsService.trackEvent(eventType, eventData);
export const trackPageView = (pageData) => analyticsService.trackPageView(pageData);
export const trackAnalysisStart = (inputType, metadata) => analyticsService.trackAnalysisStart(inputType, metadata);
export const trackAnalysisComplete = (result, metadata) => analyticsService.trackAnalysisComplete(result, metadata);
export const trackFeedback = (submission, analysisId) => analyticsService.trackFeedback(submission, analysisId);
export const trackError = (error, context) => analyticsService.trackError(error, context);
export const getAnalyticsSummary = (timeRange) => analyticsService.getAnalyticsSummary(timeRange);
export const exportAnalyticsData = (format, filters) => analyticsService.exportAnalyticsData(format, filters);
export const initializeAnalytics = () => analyticsService.initialize();
export const setAnalyticsUser = (userId) => analyticsService.setUser(userId);
export const clearAnalyticsUser = () => analyticsService.clearUser();