import React, { createContext, useState, useEffect, useContext, useCallback } from 'react';

const AnalyticsContext = createContext();

export const AnalyticsProvider = ({ children }) => {
    const [analytics, setAnalytics] = useState({
        totalAnalyses: 0,
        scamsDetected: 0,
        legitimateCount: 0,
        suspiciousCount: 0,
        accuracyRate: 0,
        userAnalytics: [],
        recentActivity: [],
        loading: false,
        error: null
    });

    const [userStats, setUserStats] = useState(() => {
        const stored = localStorage.getItem('userStats');
        return stored ? JSON.parse(stored) : {
            totalAnalyses: 0,
            scamsDetected: 0,
            avgRating: 0,
            todayAnalyses: 0,
            weekAnalyses: 0,
            monthAnalyses: 0
        };
    });

    const [history, setHistory] = useState([]);
    const [historyLoading, setHistoryLoading] = useState(false);

    // Helper to fix date formats
    const translationDateTimeFix = useCallback((dateStr) => {
        if (!dateStr) return null;
        try {
            const d = new Date(dateStr);
            return isNaN(d.getTime()) ? null : d.toISOString();
        } catch(e) { return null; }
    }, []);

    const fetchAnalytics = useCallback(async () => {
        const token = localStorage.getItem('token');
        if (!token) {
            setAnalytics(prev => ({ ...prev, loading: false }));
            return;
        }

        setAnalytics(prev => ({ ...prev, loading: true, error: null }));
        try {
            const { analysisAPI } = await import('../services/api');
            const [userStatsRes, distributionRes] = await Promise.all([
                analysisAPI.getStats(),
                analysisAPI.getDistribution()
            ]);
            
            const stats = userStatsRes.data;
            const dist = distributionRes.data;
            
            const newStats = {
                totalAnalyses: stats.total_analyses || 0,
                scamsDetected: stats.scams_detected || 0,
                legitimateFound: stats.legitimate_found || 0,
                suspiciousFound: stats.suspicious_found || 0,
                avgRiskScore: stats.avg_risk_score || 0
            };
            setUserStats(newStats);
            localStorage.setItem('userStats', JSON.stringify(newStats));
            
            setAnalytics(prev => ({
                ...prev,
                totalAnalyses: stats.total_analyses || 0,
                scamsDetected: stats.scams_detected || 0,
                legitimateCount: dist.legitimate || 0,
                suspiciousCount: dist.suspicious || 0,
                loading: false
            }));
        } catch (error) {
            console.error('Error fetching analytics:', error);
            setAnalytics(prev => ({ 
                ...prev, 
                loading: false, 
                error: (error.response?.status === 401 || error.response?.status === 403) 
                    ? null 
                    : (error.response?.data?.error || 'Failed to fetch analytics')
            }));
        }
    }, []);

    const getAnalysisHistory = useCallback(async (page = 1, limit = 100) => {
        setHistoryLoading(true);
        try {
            const { analysisAPI } = await import('../services/api');
            const response = await analysisAPI.getHistory(page, limit);
            const backendData = response.data.analyses || [];
            
            const mapped = backendData.map(item => ({
                ...item,
                id: item._id || item.id,
                _id: item._id || item.id
            }));
            
            const userStr = localStorage.getItem('user');
            const userEmail = userStr ? JSON.parse(userStr)?.email?.toLowerCase() : null;
            const localHistoryRaw = JSON.parse(localStorage.getItem('analysisHistory') || '[]');
            
            const userLocalHistory = localHistoryRaw.filter(item => {
                if (!userEmail || item.user_email?.toLowerCase() !== userEmail) return false;
                
                const localId = item.id || item._id;
                const existsById = mapped.some(remote => remote.id === localId || remote._id === localId);
                if (existsById) return false;

                const existsByContent = mapped.some(remote => {
                    const contentMatch = (remote.content === item.content) || (remote.text === item.text);
                    if (!contentMatch) return false;
                    
                    const remoteTime = new Date(remote.created_at).getTime();
                    const localTime = new Date(item.created_at).getTime();
                    return Math.abs(remoteTime - localTime) < 300000;
                });
                
                return !existsByContent;
            }).map(item => ({ ...item, id: item._id || item.id, isLocalOnly: true }));

            const merged = [...mapped, ...userLocalHistory].sort((a, b) => 
                new Date(b.created_at || b.date) - new Date(a.created_at || a.date)
            );
            
            setHistory(merged);
            return merged;
        } catch (error) {
            console.error('getAnalysisHistory error:', error);
            const localHistory = JSON.parse(localStorage.getItem('analysisHistory') || '[]');
            const userStr = localStorage.getItem('user');
            const userEmail = userStr ? JSON.parse(userStr)?.email?.toLowerCase() : null;
            const filtered = localHistory
                .filter(item => {
                    if (!userEmail) return false;
                    return item.user_email?.toLowerCase() === userEmail;
                })
                .map(item => ({ ...item, id: item._id || item.id || item.analysis_id, isLocalOnly: true }));
            
            setHistory(filtered);
            return filtered;
        } finally {
            setHistoryLoading(false);
        }
    }, []);

    const trackAnalysis = useCallback(async (analysisData) => {
        const userStr = localStorage.getItem('user');
        const currentUser = userStr ? JSON.parse(userStr) : null;
        
        const newEntry = {
            ...analysisData,
            user_email: currentUser?.email || localStorage.getItem('userEmail'),
            created_at: translationDateTimeFix(analysisData.created_at) || new Date().toISOString(),
            id: analysisData.analysis_id || analysisData._id || analysisData.id || ('local-' + Date.now()),
            _id: analysisData.analysis_id || analysisData._id || analysisData.id || ('local-' + Date.now()),
            isLocalOnly: true
        };

        setHistory(prev => [newEntry, ...prev]);

        setUserStats(prev => {
            const newStats = {
                ...prev,
                totalAnalyses: (prev.totalAnalyses || 0) + 1,
                scamsDetected: (analysisData.risk_score > 60 || analysisData.score > 60) ? (prev.scamsDetected || 0) + 1 : (prev.scamsDetected || 0)
            };
            localStorage.setItem('userStats', JSON.stringify(newStats));
            return newStats;
        });

        try {
            const localHistory = JSON.parse(localStorage.getItem('analysisHistory') || '[]');
            localHistory.unshift(newEntry);
            localStorage.setItem('analysisHistory', JSON.stringify(localHistory.slice(0, 100)));
        } catch(e) { console.error("Local save failed", e); }
        
        setTimeout(async () => {
            await fetchAnalytics();
            await getAnalysisHistory(1, 100);
        }, 1000);
    }, [fetchAnalytics, getAnalysisHistory, translationDateTimeFix]);

    const trackUserAction = useCallback(async (action, data = {}) => {
        console.log('User action tracked:', action, data);
    }, []);

    const deleteAnalysis = useCallback(async (analysisId) => {
        setHistory(prev => prev.filter(item => (item.id !== analysisId) && (item._id !== analysisId)));

        try {
            const { analysisAPI } = await import('../services/api');
            if (!String(analysisId).startsWith('local-')) {
                await analysisAPI.deleteAnalysis(analysisId);
            }
        } catch (error) {
            console.error('Backend delete failed:', error);
            if (error.response?.status !== 404 && !String(analysisId).startsWith('local-')) {
                throw error;
            }
        }

        try {
            const localHistory = JSON.parse(localStorage.getItem('analysisHistory') || '[]');
            const updated = localHistory.filter(item => 
                (item._id !== analysisId) && (item.id !== analysisId) && (item.analysis_id !== analysisId)
            );
            localStorage.setItem('analysisHistory', JSON.stringify(updated));
        } catch(e) { }

        setUserStats(prev => ({
            ...prev,
            totalAnalyses: Math.max(0, (prev.totalAnalyses || 1) - 1)
        }));

        await fetchAnalytics();
        return true;
    }, [fetchAnalytics]);

    const getTopScamCompanies = useCallback(async () => {
        return [
            { name: 'Fake Tech Solutions', reports: 45 },
            { name: 'Remote Work Hub', reports: 32 },
            { name: 'Data Entry Jobs Ltd', reports: 28 }
        ];
    }, []);

    const getRiskDistribution = useCallback(async () => {
        try {
            const { analysisAPI } = await import('../services/api');
            const response = await analysisAPI.getDistribution();
            return response.data;
        } catch (error) {
            console.error('Error fetching distribution:', error);
            return { legitimate: 0, suspicious: 0, scam: 0 };
        }
    }, []);

    const getTrendData = useCallback(async (period = 'week') => {
        try {
            const { analysisAPI } = await import('../services/api');
            const response = await analysisAPI.getTrends();
            return response.data || [];
        } catch (error) {
            console.error('Error fetching trends:', error);
            return [];
        }
    }, []);

    const exportAnalyticsData = useCallback(async (format = 'csv') => {
        const historyData = await getAnalysisHistory();
        const data = historyData.map(item => ({
            id: item._id,
            type: item.input_type,
            score: item.risk_score,
            category: item.risk_level,
            date: item.created_at
        }));
        
        let content, mimeType, extension;
        if (format === 'json') {
            content = JSON.stringify(data, null, 2);
            mimeType = 'application/json';
            extension = 'json';
        } else {
            const headers = 'ID,Type,Score,Category,Date\n';
            const rows = data.map(d => `${d.id},${d.type},${d.score},${d.category},${d.date}`).join('\n');
            content = headers + rows;
            mimeType = 'text/csv';
            extension = 'csv';
        }
        
        const blob = new Blob([content], { type: mimeType });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `scamradar-analytics-${new Date().toISOString().split('T')[0]}.${extension}`);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
        
        return true;
    }, [getAnalysisHistory]);

    useEffect(() => {
        fetchAnalytics();
    }, [fetchAnalytics]);

    const value = {
        analytics,
        userStats,
        fetchAnalytics,
        fetchUserAnalytics: fetchAnalytics,
        trackAnalysis,
        trackUserAction,
        getAnalysisHistory,
        getTopScamCompanies,
        getRiskDistribution,
        getTrendData,
        exportAnalyticsData,
        refreshAnalytics: fetchAnalytics,
        setUserStats,
        deleteAnalysis,
        history,
        historyLoading
    };

    return (
        <AnalyticsContext.Provider value={value}>
            {children}
        </AnalyticsContext.Provider>
    );
};

export const useAnalytics = () => {
    const context = useContext(AnalyticsContext);
    if (!context) {
        throw new Error('useAnalytics must be used within an AnalyticsProvider');
    }
    return context;
};

export { AnalyticsContext };
export default AnalyticsContext;