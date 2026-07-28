import React from 'react';
import { FaTimes } from 'react-icons/fa';
import { useModals } from '../context/ModalContext';
import { useTranslation } from 'react-i18next';
import './LegalModals.css';

const LegalModals = () => {
    const { activeModal, closeModal } = useModals();
    const { t } = useTranslation();

    if (!activeModal || activeModal === 'settings') return null;

    return (
        <div className="modal-overlay" onClick={closeModal}>
            <div className="modal-content legal-modal-premium" onClick={e => e.stopPropagation()}>
                <div className="modal-header">
                    <h2>{activeModal === 'privacy' ? t("legal.privacyTitle") : t("legal.termsTitle")}</h2>
                    <button className="close-btn" onClick={closeModal}><FaTimes /></button>
                </div>
                <div className="modal-body">
                    {activeModal === 'privacy' ? (
                        <div className="legal-text">
                            <p><strong>{t("legal.privacy.intro")}</strong> {t("legal.privacy.introDesc")}</p>
                            <ul>
                                <li><strong>{t("legal.privacy.anonymization")}</strong> {t("legal.privacy.anonymizationDesc")}</li>
                                <li><strong>{t("legal.privacy.noPersonalData")}</strong> {t("legal.privacy.noPersonalDataDesc")}</li>
                                <li><strong>{t("legal.privacy.dataOwnership")}</strong> {t("legal.privacy.dataOwnershipDesc")}</li>
                                <li><strong>{t("legal.privacy.security")}</strong> {t("legal.privacy.securityDesc")}</li>
                            </ul>
                        </div>
                    ) : (
                        <div className="legal-text">
                            <p>{t("legal.terms.intro")}</p>
                            <ul>
                                <li><strong>{t("legal.terms.informational")}</strong> {t("legal.terms.informationalDesc")}</li>
                                <li><strong>{t("legal.terms.educational")}</strong> {t("legal.terms.educationalDesc")}</li>
                                <li><strong>{t("legal.terms.responsibility")}</strong> {t("legal.terms.responsibilityDesc")}</li>
                                <li><strong>{t("legal.terms.fairUse")}</strong> {t("legal.terms.fairUseDesc")}</li>
                            </ul>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default LegalModals;
