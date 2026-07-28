import React, { useState, useContext, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { LanguageContext } from "../context/LanguageContext";
import { useAuth } from "../context/AuthContext";
import {
  FaPaperPlane,
  FaTrash,
  FaChevronDown,
  FaExclamationCircle,
} from "react-icons/fa";
import "./Home.css";

const PLATFORMS = [
  { value: "linkedin", icon: "💼" },
  { value: "naukri_indeed", icon: "📋" },
  { value: "email_hr", icon: "✉️" },
  { value: "whatsapp_telegram", icon: "💬" },
  { value: "referral", icon: "🤝" },
  { value: "other", icon: "🔍" },
];

const Home = () => {
  const [sourcePlatform, setSourcePlatform] = useState("");
  const [hasEmailDetails, setHasEmailDetails] = useState(false);
  const [formData, setFormData] = useState({
    content: "",
    companyName: "",
    senderEmail: "",
    companyWebsite: "",
    suspiciousDetails: "",
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

  const { t } = useContext(LanguageContext);
  const { user } = useAuth();
  const navigate = useNavigate();

  // Determine which conditional fields to show
  const showEmailFields =
    hasEmailDetails || sourcePlatform === "email_hr";
  const showWebsiteField =
    hasEmailDetails ||
    ["linkedin", "naukri_indeed", "email_hr", "referral"].includes(sourcePlatform);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    // Clear error on change
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: "" }));
    }
  };

  const validate = () => {
    const newErrors = {};

    // Content validation: min 20 chars
    if (!formData.content || formData.content.trim().length < 20) {
      newErrors.content =
        t("analysis.validation.contentMin") ||
        "Content must be at least 20 characters long";
    }

    // Company name: min 2 chars
    if (!formData.companyName || formData.companyName.trim().length < 2) {
      newErrors.companyName =
        t("analysis.validation.companyMin") ||
        "Company name must be at least 2 characters";
    }

    // Platform required
    if (!sourcePlatform) {
      newErrors.sourcePlatform =
        t("analysis.validation.platformRequired") ||
        "Please select a source platform";
    }

    // Email validation if visible and filled
    if (showEmailFields && formData.senderEmail) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(formData.senderEmail)) {
        newErrors.senderEmail =
          t("analysis.validation.emailInvalid") ||
          "Please enter a valid email address";
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    if (!validate()) return;

    setLoading(true);

    // Map to the payload structure Scan.jsx expects
    const mappedFormData = {
      jobDescription: formData.content,
      emailContent: formData.content,
      companyName: formData.companyName,
      senderEmail: formData.senderEmail || "",
      senderDomain: formData.companyWebsite
        ? formData.companyWebsite.replace(/^https?:\/\//, "").replace(/\/.*$/, "")
        : "",
      notes: formData.suspiciousDetails || "",
      sourcePlatform: sourcePlatform,
    };

    // Determine input_type for backend based on platform
    const inputType = sourcePlatform === "email_hr" ? "email" : "job";

    navigate("/scan", {
      state: {
        formData: mappedFormData,
        inputType,
      },
    });
  };

  const handleClear = () => {
    setFormData({
      content: "",
      companyName: "",
      senderEmail: "",
      companyWebsite: "",
      suspiciousDetails: "",
    });
    setSourcePlatform("");
    setHasEmailDetails(false);
    setErrors({});
  };

  return (
    <div className="home-container">
      <div className="welcome-section">
        <div className="welcome-header">
          {user ? (
            <h1>
              {t("home.welcomeUser", {
                name: user.full_name || user.name || user.email?.split("@")[0] || "User",
              })}
            </h1>
          ) : (
            <h1>{t("home.welcome")}</h1>
          )}
          <p>{t("home.subtitle")}</p>
        </div>
      </div>

      <div className="main-content">
        <div className="analysis-card">
          <h2>{t("analysis.title")}</h2>
          <p className="subtitle">{t("analysis.subtitle")}</p>

          <form onSubmit={handleSubmit} className="analysis-form vertical-layout">
            {/* ===== SOURCE PLATFORM (TOP) ===== */}
            <div className="form-section required">
              <h3>
                <span className="dot"></span> {t("analysis.requiredFields")}
              </h3>

              <div className={`field-group ${errors.sourcePlatform ? "has-error" : ""}`}>
                <label>{t("analysis.labelSourcePlatform")}</label>
                <div className="select-wrapper">
                  <select
                    value={sourcePlatform}
                    onChange={(e) => {
                      setSourcePlatform(e.target.value);
                      if (errors.sourcePlatform) {
                        setErrors((prev) => ({ ...prev, sourcePlatform: "" }));
                      }
                    }}
                    className="platform-select"
                  >
                    <option value="">{t("analysis.selectPlatform")}</option>
                    {PLATFORMS.map((p) => (
                      <option key={p.value} value={p.value}>
                        {p.icon} {t(`analysis.platforms.${p.value}`)}
                      </option>
                    ))}
                  </select>
                  <FaChevronDown className="select-arrow" />
                </div>
                {errors.sourcePlatform && (
                  <span className="field-error">
                    <FaExclamationCircle /> {errors.sourcePlatform}
                  </span>
                )}
              </div>

              {/* ===== CONTENT FIELD (ALWAYS VISIBLE) ===== */}
              <div className={`field-group ${errors.content ? "has-error" : ""}`}>
                <label>{t("analysis.labelDescription")}</label>
                <textarea
                  name="content"
                  value={formData.content}
                  onChange={handleInputChange}
                  placeholder={t("analysis.placeholderContent")}
                  rows="6"
                />
                <div className="field-meta">
                </div>
                {errors.content && (
                  <span className="field-error">
                    <FaExclamationCircle /> {errors.content}
                  </span>
                )}
              </div>

              {/* ===== COMPANY NAME (ALWAYS VISIBLE) ===== */}
              <div className={`field-group ${errors.companyName ? "has-error" : ""}`}>
                <label>{t("analysis.labelCompany")}</label>
                <input
                  type="text"
                  name="companyName"
                  value={formData.companyName}
                  onChange={handleInputChange}
                  placeholder={t("analysis.labelCompanyPlaceholder") || "e.g., Infosys Ltd., TCS, Unknown"}
                />
                {errors.companyName && (
                  <span className="field-error">
                    <FaExclamationCircle /> {errors.companyName}
                  </span>
                )}
              </div>
            </div>

            {/* ===== CONDITIONAL DYNAMIC FIELDS ===== */}
            <div className={`conditional-fields ${showEmailFields || showWebsiteField ? "visible" : ""}`}>
              {(showEmailFields || showWebsiteField) && (
                <div className="form-section conditional">
                  <h3>
                    <span className="dot blue"></span>{" "}
                    {sourcePlatform === "email_hr"
                      ? "Additional Email Details"
                      : t("analysis.optionalFields")}
                  </h3>

                  {/* Sender Email */}
                  {showEmailFields && (
                    <div className={`field-group fade-in ${errors.senderEmail ? "has-error" : ""}`}>
                      <label>{t("analysis.labelSenderEmail")}</label>
                      <input
                        type="email"
                        name="senderEmail"
                        value={formData.senderEmail}
                        onChange={handleInputChange}
                        placeholder={t("analysis.labelSenderEmailPlaceholder") || "hr@company.com"}
                      />
                      {errors.senderEmail && (
                        <span className="field-error">
                          <FaExclamationCircle /> {errors.senderEmail}
                        </span>
                      )}
                    </div>
                  )}

                  {/* Company Website */}
                  {showWebsiteField && (
                    <div className="field-group fade-in">
                      <label>{t("analysis.labelCompanyWebsite")}</label>
                      <input
                        type="text"
                        name="companyWebsite"
                        value={formData.companyWebsite}
                        onChange={handleInputChange}
                        placeholder={t("analysis.labelCompanyWebsitePlaceholder") || "https://company.com"}
                      />
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* ===== OVERRIDE CHECKBOX ===== */}
            {sourcePlatform && sourcePlatform !== "email_hr" && (
              <div className="checkbox-section fade-in">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={hasEmailDetails}
                    onChange={(e) => setHasEmailDetails(e.target.checked)}
                  />
                  <span className="checkmark"></span>
                  {t("analysis.hasEmailDetails") || "I have email details"}
                </label>
              </div>
            )}

            {/* ===== SUSPICIOUS DETAILS (ALWAYS AT BOTTOM) ===== */}
            <div className="form-section optional">
              <h3>
                <span className="dot gray"></span>{" "}
                {t("analysis.optionalFields")}
              </h3>

              <div className="field-group">
                <label>{t("analysis.labelSuspiciousDetails")}</label>
                <textarea
                  name="suspiciousDetails"
                  value={formData.suspiciousDetails}
                  onChange={handleInputChange}
                  placeholder={t("analysis.labelSuspiciousPlaceholder") || "Mention anything unusual..."}
                  rows="3"
                />
              </div>
            </div>

            {/* ===== ACTION BUTTONS ===== */}
            <div className="action-buttons">
              <button
                type="submit"
                className="btn analyze-btn"
                disabled={loading}
              >
                <FaPaperPlane /> {t("analysis.btnAnalyze")}
              </button>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={handleClear}
              >
                <FaTrash /> {t("analysis.btnClear")}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Home;
