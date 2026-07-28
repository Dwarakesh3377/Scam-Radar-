import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

import en from './en.json';
import ta from './ta.json';
import hi from './hi.json';
import fr from './fr.json';
import es from './es.json';
import de from './de.json';
import ja from './ja.json';
import zh from './zh.json';
import ru from './ru.json';
import ko from './ko.json';

i18n
    .use(LanguageDetector)
    .use(initReactI18next)
    .init({
        resources: {
            en: { translation: en },
            ta: { translation: ta },
            hi: { translation: hi },
            fr: { translation: fr },
            es: { translation: es },
            de: { translation: de },
            ja: { translation: ja },
            zh: { translation: zh },
            ru: { translation: ru },
            ko: { translation: ko }
        },
        fallbackLng: 'en',
        debug: import.meta.env.DEV,
        interpolation: {
            escapeValue: false
        },
        detection: {
            order: ['localStorage', 'navigator'],
            caches: ['localStorage']
        }
    });

export default i18n;