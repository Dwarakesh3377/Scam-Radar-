import React, { createContext, useState, useEffect, useContext } from 'react';
import { useTranslation } from 'react-i18next';
import i18n from '../i18n';

const LanguageContext = createContext();

export const LanguageProvider = ({ children }) => {
    const { t } = useTranslation();
    const [language, setLanguage] = useState(() => {
        return localStorage.getItem('language') || i18n.language || 'en';
    });

    const languages = [
        { code: 'en', name: 'English', nativeName: 'English', flag: '🇺🇸' },
        { code: 'ta', name: 'Tamil', nativeName: 'தமிழ்', flag: '🇮🇳' },
        { code: 'hi', name: 'Hindi', nativeName: 'हिन्दी', flag: '🇮🇳' },
        { code: 'fr', name: 'French', nativeName: 'Français', flag: '🇫🇷' },
        { code: 'es', name: 'Spanish', nativeName: 'Español', flag: '🇪🇸' },
        { code: 'de', name: 'German', nativeName: 'Deutsch', flag: '🇩🇪' },
        { code: 'ja', name: 'Japanese', nativeName: '日本語', flag: '🇯🇵' },
        { code: 'zh', name: 'Chinese', nativeName: '中文', flag: '🇨🇳' },
        { code: 'ru', name: 'Russian', nativeName: 'Русский', flag: '🇷🇺' },
        { code: 'ko', name: 'Korean', nativeName: '한국어', flag: '🇰🇷' }
    ];

    useEffect(() => {
        if (language !== i18n.language) {
            i18n.changeLanguage(language);
        }
        localStorage.setItem('language', language);
    }, [language]);

    const changeLanguage = (langCode) => {
        setLanguage(langCode);
    };

    return (
        <LanguageContext.Provider value={{ 
            language, 
            languages, 
            changeLanguage, 
            t 
        }}>
            {children}
        </LanguageContext.Provider>
    );
};

export const useLanguage = () => useContext(LanguageContext);
export { LanguageContext };
export default LanguageContext;
