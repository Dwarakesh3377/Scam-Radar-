import React, { createContext, useState, useContext } from 'react';

const ModalContext = createContext();

export const ModalProvider = ({ children }) => {
    const [activeModal, setActiveModal] = useState(null); // 'privacy', 'terms', 'settings'

    const openPrivacy = () => setActiveModal('privacy');
    const openTerms = () => setActiveModal('terms');
    const openSettings = () => setActiveModal('settings');
    const closeModal = () => setActiveModal(null);

    return (
        <ModalContext.Provider value={{ 
            activeModal, 
            openPrivacy, 
            openTerms, 
            openSettings, 
            closeModal 
        }}>
            {children}
        </ModalContext.Provider>
    );
};

export const useModals = () => {
    const context = useContext(ModalContext);
    if (!context) {
        throw new Error('useModals must be used within a ModalProvider');
    }
    return context;
};

export default ModalContext;
