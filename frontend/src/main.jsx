import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import App from "./App";
import "./i18n";
import "./index.css";

// Theme initialization
const initializeTheme = () => {
  const savedTheme = localStorage.getItem("theme");
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;

  if (savedTheme) {
    document.documentElement.setAttribute("data-theme", savedTheme);
  } else if (prefersDark) {
    document.documentElement.setAttribute("data-theme", "dark");
  } else {
    document.documentElement.setAttribute("data-theme", "light");
  }
};

// Language initialization
const initializeLanguage = () => {
  const savedLanguage = localStorage.getItem("language");
  const browserLanguage = navigator.language.split("-")[0];
  const supportedLanguages = [
    "en",
    "ta",
    "hi",
    "fr",
    "es",
    "de",
    "ja",
    "zh",
    "ru",
    "ko",
  ];

  if (savedLanguage) {
    document.documentElement.lang = savedLanguage;
  } else if (supportedLanguages.includes(browserLanguage)) {
    document.documentElement.lang = browserLanguage;
  } else {
    document.documentElement.lang = "en";
  }
};

// Error boundary component
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("React Error Boundary:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary">
          <div className="error-content">
            <h1>🛡️ ScamRadar</h1>
            <h2>Something went wrong</h2>
            <p>We're sorry, but an unexpected error occurred.</p>
            <button onClick={() => window.location.reload()} className="btn">
              Reload Page
            </button>
            <button
              onClick={() => {
                this.setState({ hasError: false });
                window.location.href = "/";
              }}
              className="btn btn-secondary"
              style={{ marginLeft: "10px" }}
            >
              Go to Home
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Initialize before rendering
initializeTheme();
initializeLanguage();

// Create root and render
const rootElement = document.getElementById("root");

if (!rootElement) {
  throw new Error("Root element not found");
}

const root = ReactDOM.createRoot(rootElement);

root.render(
  <React.StrictMode>
    <BrowserRouter>
      <ErrorBoundary>
        <App />
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: "var(--bg-secondary)",
              color: "var(--text-primary)",
              border: "1px solid var(--accent-cyan)",
              boxShadow: "0 0 15px rgba(0, 255, 255, 0.3)",
            },
            success: {
              iconTheme: {
                primary: "#00ff00",
                secondary: "#1a1a2e",
              },
            },
            error: {
              iconTheme: {
                primary: "#ff0000",
                secondary: "#1a1a2e",
              },
            },
          }}
        />
      </ErrorBoundary>
    </BrowserRouter>
  </React.StrictMode>,
);
