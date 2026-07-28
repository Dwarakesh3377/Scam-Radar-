import React, { useState, useEffect } from "react";
import { useNavigate, useLocation, useSearchParams } from "react-router-dom";
import {
  FiMail,
  FiLock,
  FiArrowRight,
} from "react-icons/fi";
import { FaGithub, FaEnvelope, FaLock, FaUser, FaArrowRight, FaEye, FaEyeSlash } from "react-icons/fa";
import { FcGoogle } from "react-icons/fc";
import { useAuth } from "../context/AuthContext";
import { useTranslation } from "react-i18next";
import { useModals } from "../context/ModalContext";
import toast from "react-hot-toast";
import "./Auth.css";

const Auth = () => {
  const { openPrivacy, openTerms } = useModals();
  const { user, login, signup, socialLogin, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();
  const autoSocial = searchParams.get('auto_social');
  const { t } = useTranslation();

  const [isLogin, setIsLogin] = useState(location.pathname === "/login" || location.pathname === "/");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [formData, setFormData] = useState({
    firstName: "",
    lastName: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user && !authLoading) {
      const from = location.state?.from?.pathname || "/";
      navigate(from, { replace: true });
    }
  }, [user, authLoading, navigate, location]);

  useEffect(() => {
    if (location.pathname === "/signup") {
      setIsLogin(false);
    } else if (location.pathname === "/login") {
      setIsLogin(true);
    }
  }, [location.pathname]);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleAuthSubmit = async (e, formType) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (formType === 'login') {
        await login({ email: formData.email, password: formData.password });
        toast.success(t("common.success") || "Logged in successfully!");
        navigate("/");
      } else {
        if (formData.password !== formData.confirmPassword) {
          toast.error("Passwords do not match");
          setLoading(false);
          return;
        }
        await signup({
          fullName: `${formData.firstName} ${formData.lastName}`.trim(),
          username: formData.email.split('@')[0],
          email: formData.email,
          password: formData.password,
        });
        toast.success(t("common.success") || "Account created successfully!");
        navigate("/");
      }
    } catch (err) {
      console.error("Auth error:", err);
      const errorMessage = err.message || 
                         err.response?.data?.error || 
                         err.response?.data?.message || 
                         "Authentication failed";
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleSocialSubmit = async (provider) => {
    // DIRECT POPUP: Firebase domains are now authorized, so popup works directly.
    // No iframe breakout needed — Google/GitHub popup opens on top of everything.
    setLoading(true);
    try {
      const userData = await socialLogin(provider);
      if (userData) {
        toast.success(t("common.success") || "Signed in successfully!");
        navigate("/", { replace: true });
      }
    } catch (err) {
      console.error(`${provider} auth error:`, err);
      toast.error(err.message || "Authentication failed");
    } finally {
      setLoading(false);
    }
  };

  // --- UI RENDER ---
  return (
    <div className="auth-page-wrapper">
      <div className={`auth-card-container double-layout ${!isLogin ? "right-panel-active" : ""}`}>
        
        {/* Sign Up Container */}
        <div className="form-container sign-up-container">
          <form onSubmit={(e) => handleAuthSubmit(e, "signup")} className="auth-form">
            <div className="auth-header">
              <h2>{t("auth.createAccount", "Create Account")}</h2>
            </div>

            
            <div className="grid-form">
              <div className="form-group">
                <label>{t("auth.firstName", "First Name")}</label>
                <div className="input-with-icon">
                  <FaUser className="input-icon" />
                  <input 
                    type="text" 
                    name="firstName" 
                    placeholder={t("auth.firstName", "First Name")}
                    value={formData.firstName}
                    onChange={handleChange}
                    required 
                  />
                </div>
              </div>
              <div className="form-group">
                <label>{t("auth.lastName", "Last Name")}</label>
                <div className="input-with-icon">
                  <FaUser className="input-icon" />
                  <input 
                    type="text" 
                    name="lastName" 
                    placeholder={t("auth.lastName", "Last Name")}
                    value={formData.lastName}
                    onChange={handleChange}
                    required 
                  />
                </div>
              </div>
            </div>

            <div className="form-group">
              <label>{t("auth.email", "Email Address")}</label>
              <div className="input-with-icon">
                <FiMail className="input-icon" />
                <input 
                  type="email" 
                  name="email" 
                  placeholder="name@example.com"
                  value={formData.email}
                  onChange={handleChange}
                  required 
                />
              </div>
            </div>

            <div className="grid-form">
              <div className="form-group">
                <label>{t("auth.password", "Password")}</label>
                <div className="input-with-icon">
                  <FiLock className="input-icon" />
                  <input 
                    type={showPassword ? "text" : "password"} 
                    name="password" 
                    placeholder="••••••••"
                    value={formData.password}
                    onChange={handleChange}
                    required 
                  />
                  <button type="button" className="password-toggle" onClick={() => setShowPassword(!showPassword)}>
                    {showPassword ? <FaEyeSlash /> : <FaEye />}
                  </button>
                </div>
              </div>
              <div className="form-group">
                <label>{t("auth.confirmPassword", "Confirm")}</label>
                <div className="input-with-icon">
                  <FiLock className="input-icon" />
                  <input 
                    type={showConfirmPassword ? "text" : "password"} 
                    name="confirmPassword" 
                    placeholder="••••••••"
                    value={formData.confirmPassword}
                    onChange={handleChange}
                    required 
                  />
                  <button type="button" className="password-toggle" onClick={() => setShowConfirmPassword(!showConfirmPassword)}>
                    {showConfirmPassword ? <FaEyeSlash /> : <FaEye />}
                  </button>
                </div>
              </div>
            </div>

            <button type="submit" className="neon-btn" disabled={loading || authLoading}>
              {loading || authLoading ? <div className="loader"></div> : t("auth.signUp", "Sign Up")}
              {!loading && !authLoading && <FiArrowRight />}
            </button>

            <div className="auth-legal-info">
               {t("auth.agreement", "By signing up, you agree to our")} 
               <button type="button" className="link-style-btn" onClick={openTerms}> {t("settings.terms")} </button>
               {' & '}
               <button type="button" className="link-style-btn" onClick={openPrivacy}> {t("settings.privacy")} </button>
            </div>
          </form>
        </div>

        {/* Sign In Container */}
        <div className="form-container sign-in-container">
          <form onSubmit={(e) => handleAuthSubmit(e, "login")} className="auth-form">
            <div className="auth-header">
              <h2>{t("auth.welcomeBackHeader", "Welcome Back!")}</h2>
            </div>


            <div className="form-group">
              <label>{t("auth.email", "Email Address")}</label>
              <div className="input-with-icon">
                <FiMail className="input-icon" />
                <input 
                  type="email" 
                  name="email" 
                  placeholder="name@example.com"
                  value={formData.email}
                  onChange={handleChange}
                  required 
                />
              </div>
            </div>

            <div className="form-group">
              <label>{t("auth.password", "Password")}</label>
              <div className="input-with-icon">
                <FiLock className="input-icon" />
                <input 
                  type={showPassword ? "text" : "password"} 
                  name="password" 
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={handleChange}
                  required 
                />
                <button type="button" className="password-toggle" onClick={() => setShowPassword(!showPassword)}>
                  {showPassword ? <FaEyeSlash /> : <FaEye />}
                </button>
              </div>
            </div>

            <button type="submit" className="neon-btn" disabled={loading || authLoading}>
              {loading || authLoading ? <div className="loader"></div> : t("auth.login", "Login")}
              {!loading && !authLoading && <FiArrowRight />}
            </button>
          </form>
        </div>

        {/* Overlay Container */}
        <div className="overlay-container">
          <div className="overlay">
            <div className="overlay-panel overlay-left">
              <h2>{t("auth.welcomeBackTitle", "Welcome Back!")}</h2>
              <p>{t("auth.hasAccount", "Already have an account?")}</p>
              <button className="ghost-btn" onClick={() => setIsLogin(true)}>
                {t("auth.signIn", "Login")}
              </button>
              
              <div className="auth-divider"><span>{t("auth.or", "OR")}</span></div>
              <div className="social-auth-container">
                <button 
                  type="button"
                  className="social-full-btn"
                  onClick={() => handleSocialSubmit('google')}
                  disabled={loading || authLoading}
                >
                  <FcGoogle fontSize="1.4rem" /> {t('auth.signupWithGoogle', "Sign up with Google")}
                </button>
                <button 
                  type="button"
                  className="social-full-btn"
                  onClick={() => handleSocialSubmit('github')}
                  disabled={loading || authLoading}
                >
                  <FaGithub fontSize="1.4rem" /> {t('auth.signupWithGithub', "Sign up with GitHub")}
                </button>
              </div>
            </div>
            <div className="overlay-panel overlay-right">
              <h2>{t("auth.helloFriend", "Hello, Friend!")}</h2>
              <p>{t("auth.noAccount", "Don't have an account?")}</p>
              <button className="ghost-btn" onClick={() => setIsLogin(false)}>
                {t("auth.signUp", "Sign Up")}
              </button>
              
              <div className="auth-divider"><span>{t("auth.or", "OR")}</span></div>
              <div className="social-auth-container">
                <button 
                  type="button"
                  className="social-full-btn"
                  onClick={() => handleSocialSubmit('google')}
                  disabled={loading || authLoading}
                >
                  <FcGoogle fontSize="1.4rem" /> {t('auth.loginWithGoogle', "Login with Google")}
                </button>
                <button 
                  type="button"
                  className="social-full-btn"
                  onClick={() => handleSocialSubmit('github')}
                  disabled={loading || authLoading}
                >
                  <FaGithub fontSize="1.4rem" /> {t('auth.loginWithGithub', "Login with GitHub")}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Auth;
