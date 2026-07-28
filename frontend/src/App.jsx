import React, { useEffect } from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { LanguageProvider } from './context/LanguageContext';
import { ThemeProvider } from './context/ThemeContext';
import { AuthProvider, useAuth } from './context/AuthContext';
import { AnalyticsProvider } from './context/AnalyticsContext';
import { ModalProvider, useModals } from './context/ModalContext';
import { FeedbackProvider } from './components/FeedbackModal';
import LegalModals from './components/LegalModals';
import Navbar from './components/Navbar';
import { useTranslation } from 'react-i18next';
import Auth from './pages/Auth';
import Home from './pages/Home';
import Scan from './pages/Scan';
import Result from './pages/Result';
import Profile from './pages/Profile';
import Dashboard from './pages/Dashboard';
// import Settings from './pages/Settings'; (Deleted)
import PrivateRoute from './components/PrivateRoute';
import './App.css';

// Scroll to top component
function ScrollToTop() {
  const { pathname } = useLocation();

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);

  return null;
}

const THEME_COLORS = {
  'Cyan': '#00ffff',
  'Blue': '#007bff',
  'Purple': '#6f42c1',
  'Indigo': '#6610f2',
  'Pink': '#e83e8c',
  'NeonYellow': '#F5FF00',
  'NeonGold': '#FFD700',
  'IceBlue': '#E0FFFF',
  'SlateGrey': '#708090',
  'NeonSilver': '#C0C0FF'
};

function ThemeColorPropagator() {
  const { user } = useAuth();
  
  useEffect(() => {
    if (user && user.theme_color) {
      const colorHex = THEME_COLORS[user.theme_color] || '#00ffff';
      document.documentElement.style.setProperty('--primary-color', colorHex);
      
      // Create a glow color with transparency
      // If it's a hex like #RRGGBB, we convert it to rgba
      const r = parseInt(colorHex.slice(1, 3), 16);
      const g = parseInt(colorHex.slice(3, 5), 16);
      const b = parseInt(colorHex.slice(5, 7), 16);
      
      document.documentElement.style.setProperty('--primary-glow', `rgba(${r}, ${g}, ${b}, 0.3)`);
      document.documentElement.style.setProperty('--primary-transparent', `rgba(${r}, ${g}, ${b}, 0.1)`);
    } else {
      // Default to Cyan
      document.documentElement.style.setProperty('--primary-color', '#00ffff');
      document.documentElement.style.setProperty('--primary-glow', 'rgba(0, 255, 255, 0.3)');
      document.documentElement.style.setProperty('--primary-transparent', 'rgba(0, 255, 255, 0.1)');
    }
  }, [user?.theme_color]);

  return null;
}

function App() {
  return (
    <ThemeProvider>
      <LanguageProvider>
        <AuthProvider>
          <ModalProvider>
            <AppContent />
          </ModalProvider>
        </AuthProvider>
      </LanguageProvider>
    </ThemeProvider>
  );
}

function AppContent() {
  const { t } = useTranslation();
  const { openPrivacy, openTerms } = useModals();

  return (
    <>
      <ThemeColorPropagator />
      <AnalyticsProvider>
        <FeedbackProvider>
          <div className="App">
            <ScrollToTop />
            <Navbar />
            <LegalModals />
            <main className="main-content">
              <Routes>
                {/* Public routes */}
                <Route path="/login" element={<Auth />} />
                <Route path="/signup" element={<Auth />} />
                
                {/* Protected routes */}
                <Route path="/" element={
                  <PrivateRoute>
                    <Home />
                  </PrivateRoute>
                } />
                
                <Route path="/scan" element={
                  <PrivateRoute>
                    <Scan />
                  </PrivateRoute>
                } />
                
                <Route path="/result/:analysisId?" element={
                  <PrivateRoute>
                    <Result />
                  </PrivateRoute>
                } />
                
                
                <Route path="/profile" element={
                  <PrivateRoute>
                    <Profile />
                  </PrivateRoute>
                } />
                
                <Route path="/dashboard" element={
                  <PrivateRoute>
                    <Dashboard />
                  </PrivateRoute>
                } />
                
                {/* Settings route removed - now modal based */}
                
                {/* Redirect all other routes to home */}
                <Route path="*" element={<Navigate to="/" />} />
              </Routes>
            </main>
                
            {/* Footer */}
            <footer className="app-footer">
              <div className="footer-content">
                <div className="footer-section">
                  <h4>
                    <img src="/logo.png" alt="" style={{ width: '32px', height: '32px', verticalAlign: 'middle', marginRight: '8px', objectFit: 'contain' }} />
                    ScamRadar
                  </h4>
                  <p>{t('footer.tagline')}</p>
                </div>
                <div className="footer-section">
                  <h4>{t('footer.quickLinks')}</h4>
                  <a href="/">{t('footer.home')}</a>
                  <a href="/profile">{t('footer.profile')}</a>
                  <a href="/dashboard">{t('footer.dashboard')}</a>
                </div>
                <div className="footer-section">
                  <h4>{t('footer.legal')}</h4>
                  <button className="footer-link-btn" onClick={openPrivacy}>{t('footer.privacyPolicy')}</button>
                  <button className="footer-link-btn" onClick={openTerms}>{t('footer.termsConditions')}</button>
                </div>

              </div>
              <div className="footer-bottom">
                <p>&copy; 2026 ScamRadar. {t('footer.rights')}</p>
              </div>
            </footer>
          </div>
        </FeedbackProvider>
      </AnalyticsProvider>
    </>
  );
}

export default App;