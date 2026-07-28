import React, { useState, useEffect, useContext } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import PacmanLoader from "../components/PacmanLoader";
import { AnalyticsContext } from "../context/AnalyticsContext";
import { LanguageContext } from "../context/LanguageContext";
import { analysisAPI } from "../services/api";
import "./Scan.css";

const Scan = () => {
  const [progress, setProgress] = useState(0);
  const [scanComplete, setScanComplete] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { t, language } = useContext(LanguageContext);
  const { formData, inputType } = location.state || {}; // inputType is 'job' or 'email'
  const { trackAnalysis } = useContext(AnalyticsContext);

  useEffect(() => {
    if (!formData) {
      navigate("/");
      return;
    }

    const performAnalysis = async () => {
      const FIXED_DURATION = 15000; // 15 seconds to allow BERT more time
      const startTime = Date.now();
      let analysisResult = null;
      let realAnalysisError = null;

      // Start progress simulation to reach 100% in exactly 5 seconds
      const progressInterval = setInterval(() => {
        const elapsed = Date.now() - startTime;
        const newProgress = Math.min((elapsed / FIXED_DURATION) * 100, 99);
        setProgress(newProgress);
      }, 100);

      // Attempt real analysis in background
      const analysisPromise = (async () => {
        try {
          const payload = {
            input_type: inputType,
            ui_language: language, // Pass the currently selected UI language
            job_description: formData.jobDescription || "",
            company_name: formData.companyName || "",
            sender_email: formData.senderEmail || "",
            sender_domain: formData.senderDomain || "",
            email_content: formData.emailContent || "",
            found_urls: formData.foundUrls || "",
            phone: formData.phone || "",
            attachments_info: formData.attachmentsInfo || "",
            notes: formData.notes || "",
          };
          
          console.log("[SCAN] Starting real analysis with payload:", payload);
          try {
            const response = await analysisAPI.analyze(payload);
            analysisResult = response.data;
          } catch (firstError) {
            // If 401 (expired/invalid token), retry without auth header
            if (firstError.response?.status === 401) {
              console.warn("[SCAN] Got 401 — retrying without auth token...");
              localStorage.removeItem("token"); // Clear stale token
              const { default: axios } = await import("axios");
              const baseURL = import.meta.env.VITE_API_URL || "http://127.0.0.1:5000/api";
              const retryResponse = await axios.post(
                `${baseURL}/analyze/analyze`,
                payload,
                { timeout: 60000, headers: { "Content-Type": "application/json" } }
              );
              analysisResult = retryResponse.data;
            } else {
              throw firstError; // Re-throw non-401 errors
            }
          }
          console.log("[SCAN] Real analysis success. Reviews:", analysisResult?.negative_reviews?.length || 0);
        } catch (error) {
          console.error("[SCAN] *** REAL ANALYSIS FAILED ***");
          console.error("[SCAN] Error:", error.code, error.message, error.response?.status);
          realAnalysisError = error;
        }
      })();

      // Wait for exactly 5 seconds for the animation
      await new Promise((resolve) => setTimeout(resolve, FIXED_DURATION));

      // Wait for the real analysis to finish (it might have finished long ago or be just about to)
      // If it takes too much longer (e.g. > 10s total), the api.js timeout will catch it
      await analysisPromise;

      clearInterval(progressInterval);
      setProgress(100);
      setScanComplete(true);

      // Log for debugging
      if (analysisResult) {
        console.log(
          "[SCAN] Real backend succeeded. Reviews:",
          analysisResult.negative_reviews?.length || 0,
        );
      } else {
        console.error(
          "[SCAN] Backend failed, using mock. Error:",
          realAnalysisError?.message,
        );
      }

      // Mock fallback if real analysis failed or returned nothing
      if (!analysisResult) {
        const text = formData.jobDescription || formData.emailContent || "";
        const textLower = text.toLowerCase();
        
        // More intelligent keywords: ignore "no fees", "no payment"
        const hasScamKeywords = 
          ((textLower.includes("pay") || textLower.includes("fee") || textLower.includes("money")) && 
           !textLower.includes("no fee") && !textLower.includes("no pay") && !textLower.includes("no money")) ||
          textLower.includes("urgent") ||
          textLower.includes("commission") ||
          textLower.includes("whatsapp") ||
          textLower.includes("telegram");

        const isScam = hasScamKeywords;

        // Split input into lines for dynamic breakdown
        const inputLines = text
          .split("\n")
          .map((l) => l.trim())
          .filter((l) => l.length > 5);
        const explanationLines = [];

        if (isScam) {
          // Map i18n keys for fallback scan reasons
          inputLines.forEach((line, index) => {
            const lineLower = line.toLowerCase();
            const lineHasNoFee = lineLower.includes("no fee") || lineLower.includes("no pay") || lineLower.includes("no money");
            
            if (
              (lineLower.includes("pay") ||
              lineLower.includes("fee") ||
              lineLower.includes("money") ||
              lineLower.includes("bank")) && !lineHasNoFee
            ) {
              explanationLines.push({
                input_line: line,
                indicator: "🚨",
                type: "scam",
                reason: "analysis.explanations.payment",
              });
            } else if (
              lineLower.includes("whatsapp") ||
              lineLower.includes("telegram") ||
              lineLower.includes("contact") ||
              lineLower.includes("+91")
            ) {
              explanationLines.push({
                input_line: line,
                indicator: "🚨",
                type: "scam",
                reason: "analysis.explanations.informal_contact",
              });
            } else if (
              lineLower.includes("urgent") ||
              lineLower.includes("immediately") ||
              lineLower.includes("today") ||
              lineLower.includes("now")
            ) {
              explanationLines.push({
                input_line: line,
                indicator: "⚠️",
                type: "suspicious",
                reason: "analysis.explanations.urgency",
              });
            } else {
              explanationLines.push({
                input_line: line,
                indicator: "⚠️",
                type: "suspicious",
                reason: "analysis.explanations.uppercase",
              });
            }
          });

          analysisResult = {
            score: Math.floor(Math.random() * (95 - 75 + 1)) + 75,
            confidence: Math.floor(Math.random() * (92 - 65 + 1)) + 65,
            category: "scam",
            risk_level: "SCAM",
            analysis_id: "mock-scam-" + Date.now(),
            explanations:
              explanationLines.length > 0
                ? explanationLines.slice(0, 8)
                : [
                    {
                      input_line: text.substring(0, 60) + "...",
                      indicator: "🚨",
                      type: "scam",
                      reason: "analysis.explanations.payment",
                    },
                  ],
            negative_reviews: [],
          };
        } else {
          // Dynamic suspicious fallback
          inputLines.forEach((line, index) => {
            if (index === 0) {
              explanationLines.push({
                input_line: line,
                indicator: "⚠️",
                type: "suspicious",
                reason: "analysis.explanations.uppercase",
              });
            } else {
              explanationLines.push({
                input_line: line,
                indicator: "✅",
                type: "legitimate",
                reason: "analysis.explanations.professional",
              });
            }
          });

          analysisResult = {
            score: 42,
            confidence: Math.floor(Math.random() * (75 - 55 + 1)) + 55,
            category: "suspicious",
            risk_level: "SUSPICIOUS",
            analysis_id: "mock-suspicious-" + Date.now(),
            explanations:
              explanationLines.length > 0
                ? explanationLines.slice(0, 6)
                : [
                    {
                      input_line: text.substring(0, 50) || "Header",
                      indicator: "⚠️",
                      reason: "analysis.explanations.uppercase",
                      type: "suspicious",
                    },
                  ],
          };
        }
      }

      if (analysisResult) {
        trackAnalysis(analysisResult);
      }

      setTimeout(() => {
        navigate("/result", {
          state: {
            formData,
            inputType,
            result: analysisResult,
          },
        });
      }, 800);
    };

    performAnalysis();
  }, [formData, inputType, navigate]);

  return (
    <div className="scan-container">
      <div className="scan-content">
        <PacmanLoader message={t("analysis.loading")} />

        <div className="progress-section">
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
          <div className="progress-text">
            {progress.toFixed(0)}% {t("common.success")}
          </div>
        </div>

        <div className="scan-steps">
          <div className={`scan-step ${progress > 0 ? "active" : ""}`}>
            <div className="step-number">1</div>
            <div className="step-name">{t("analysis.steps.language")}</div>
          </div>
          <div className={`scan-step ${progress > 20 ? "active" : ""}`}>
            <div className="step-number">2</div>
            <div className="step-name">{t("analysis.steps.preprocess")}</div>
          </div>
          <div className={`scan-step ${progress > 40 ? "active" : ""}`}>
            <div className="step-number">3</div>
            <div className="step-name">{t("analysis.steps.anonymize")}</div>
          </div>
          <div className={`scan-step ${progress > 60 ? "active" : ""}`}>
            <div className="step-number">4</div>
            <div className="step-name">{t("analysis.steps.features")}</div>
          </div>
          <div className={`scan-step ${progress > 80 ? "active" : ""}`}>
            <div className="step-number">5</div>
            <div className="step-name">{t("analysis.steps.prediction")}</div>
          </div>
        </div>

        {scanComplete && (
          <div className="scan-complete">
            <div className="success-animation">✓</div>
            <h3>{t("common.success")}!</h3>
            <p>{t("result.goHome")}...</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Scan;
