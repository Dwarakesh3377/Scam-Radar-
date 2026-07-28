import React, { useContext, useState, useRef, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import { ThemeContext } from '../context/ThemeContext';
import { LanguageContext } from '../context/LanguageContext';
import { AnalyticsContext } from '../context/AnalyticsContext';
import { useModals } from '../context/ModalContext';
import { FaUser, FaUserCircle, FaUserAlt, FaCog, FaMoon, FaSun, FaGlobe, FaHome, FaSignOutAlt, FaTimes, FaShieldAlt, FaFileContract, FaUserSecret, FaTrashAlt, FaArrowLeft, FaChartBar } from 'react-icons/fa';
import { FiSettings } from 'react-icons/fi';
import { motion, AnimatePresence } from 'framer-motion';
import './Navbar.css';

const Navbar = () => {
    const { user, logout } = useContext(AuthContext);
    const { theme, toggleTheme } = useContext(ThemeContext);
    const { language, languages, changeLanguage, t } = useContext(LanguageContext);
    const { refreshAnalytics } = useContext(AnalyticsContext);
    const { openPrivacy, openTerms } = useModals();
    const navigate = useNavigate();
    const [showSettings, setShowSettings] = useState(false);
    const settingsRef = useRef(null);

    const handleLogout = () => {
        logout();
        setShowSettings(false);
        navigate('/login');
    };

    const handleClearHistory = async () => {
        if (window.confirm('Are you sure you want to clear your entire analysis history? This action cannot be undone.')) {
            try {
                // Clear local storage first for immediate feedback
                localStorage.removeItem('analysisHistory');
                
                const { analysisAPI } = await import('../services/api');
                await analysisAPI.clearHistory();
                
                alert('History cleared successfully!');
                refreshAnalytics();
                setShowSettings(false);
            } catch (error) {
                console.error('Failed to clear history:', error);
                // Even if API fails, local history is gone now
                refreshAnalytics();
                setShowSettings(false);
            }
        }
    };


    // Close dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (settingsRef.current && !settingsRef.current.contains(event.target)) {
                setShowSettings(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    return (
        <nav className="navbar">
            <div className="navbar-container">
                <div className="navbar-brand">
                    <div className="logo" style={{ display: 'flex', alignItems: 'center' }}>
                        <img src="/logo.png" alt="ScamRadar Logo" style={{ width: '64px', height: '64px', objectFit: 'contain' }} />
                    </div>
                    <Link to="/" className="app-name">ScamRadar</Link>
                </div>

                <div className="navbar-controls">
                    {user && (
                        <div className="nav-links">
                            <Link to="/" className="nav-icon-link" title={t('home')}>
                                <FaHome />
                                <span className="nav-label">Home</span>
                            </Link>
                            <Link to="/profile" className="nav-icon-link" title={t('profile')}>
                                {user?.avatar_id && user.avatar_id !== 'default' ? (
                                    <img 
                                        src={`/avatars/${encodeURIComponent(user.avatar_id)}.png`} 
                                        alt="Profile" 
                                        className="navbar-avatar-img"
                                        style={{ width: '36px', height: '36px', borderRadius: '50%', objectFit: 'cover' }}
                                        onError={(e) => { e.target.src = '/avatars/lion.png'; }}
                                    />
                                ) : (
                                    <FaUserCircle className="default-nav-icon" />
                                )}
                                <span className="nav-label">Profile</span>
                            </Link>
                            <Link to="/dashboard" className="nav-icon-link" title="Dashboard">
                                <FaChartBar />
                                <span className="nav-label">Dashboard</span>
                            </Link>
                        </div>
                    )}

                    <div className="settings-wrapper" ref={settingsRef}>
                        <button 
                            className={`nav-btn settings-trigger ${showSettings ? 'active' : ''}`} 
                            onClick={() => setShowSettings(!showSettings)}
                            title={t('settings.title')}
                        >
                            <FiSettings />
                            <span className="nav-label">Settings</span>
                        </button>

                        <AnimatePresence>
                            {showSettings && (
                                <motion.div 
                                    className="settings-dropdown"
                                    initial={{ opacity: 0, y: 10, scale: 0.95 }}
                                    animate={{ opacity: 1, y: 0, scale: 1 }}
                                    exit={{ opacity: 0, y: 10, scale: 0.95 }}
                                    transition={{ duration: 0.2 }}
                                >
                                    <div className="dropdown-header">
                                        <h3>{t('settings.title')}</h3>
                                        <button onClick={() => setShowSettings(false)} className="close-btn">
                                            <FaTimes />
                                        </button>
                                    </div>

                                    <div className="dropdown-section">
                                        <div className="section-label">
                                            <FaCog /> {t('settings.theme')}
                                        </div>
                                        <div className="theme-toggle-panel">
                                            <FaSun className={`theme-icon ${theme === 'light' ? 'active' : ''}`} />
                                            <label className="nav-theme-switch">
                                                <input 
                                                    type="checkbox" 
                                                    checked={theme === 'dark'} 
                                                    onChange={toggleTheme}
                                                />
                                                <span className="nav-theme-slider"></span>
                                            </label>
                                            <FaMoon className={`theme-icon ${theme === 'dark' ? 'active' : ''}`} />
                                        </div>
                                    </div>

                                    <div className="dropdown-section">
                                        <div className="section-label">
                                            <FaGlobe /> {t('settings.language')}
                                        </div>
                                        <div className="language-grid">
                                            {languages.map((lang) => (
                                                <button 
                                                    key={lang.code} 
                                                    className={`lang-option ${language === lang.code ? 'active' : ''}`}
                                                    onClick={() => {
                                                        changeLanguage(lang.code);
                                                    }}
                                                >
                                                    <span className="lang-code-tag">{lang.code.toUpperCase()}</span>
                                                    <span className="name">{lang.name}</span>
                                                </button>
                                            ))}
                                        </div>
                                    </div>

                                    <div className="dropdown-section">
                                        <div className="section-label">
                                            <FaShieldAlt /> {t('settings.legal')}
                                        </div>
                                        <div className="legal-links-list">
                                            <button className="legal-link-item" onClick={() => { setShowSettings(false); openPrivacy(); }}>
                                                <FaUserSecret /> {t('settings.privacy')}
                                            </button>
                                            <button className="legal-link-item" onClick={() => { setShowSettings(false); openTerms(); }}>
                                                <FaFileContract /> {t('settings.terms')}
                                            </button>

                                        </div>
                                    </div>

                                    <div className="dropdown-footer">
                                        <button onClick={handleLogout} className="logout-btn-premium">
                                            <FaSignOutAlt /> {t('settings.logout')}
                                        </button>
                                        <button className="dropdown-back-btn" onClick={() => setShowSettings(false)}>
                                            <FaArrowLeft /> Back
                                        </button>
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>
                </div>
            </div>
        </nav>
    );
};

export default Navbar;
