import React, { createContext, useState, useEffect, useContext } from "react";
import { authAPI } from "../services/api";
import { auth, googleProvider, githubProvider } from "../config/firebase";
import { signInWithPopup, signInWithRedirect, getRedirectResult } from "firebase/auth";
import toast from "react-hot-toast";

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initAuth = async () => {
      setLoading(true);
      try {
        // 1. Check for Redirect Result (Crucial for Hugging Face iframes)
        const redirectResult = await getRedirectResult(auth);
        if (redirectResult) {
          console.log("[AUTH] Completing redirect login result...");
          const idToken = await redirectResult.user.getIdToken();
          const response = await authAPI.firebaseLogin(idToken);
          const { user: userData, access_token } = response.data;

          setUser(userData);
          localStorage.setItem("user", JSON.stringify(userData));
          localStorage.setItem("token", access_token);
          toast.success("Login Successful!");
          setLoading(false);
          return;
        }

        // 2. Restore saved session
        const savedUser = localStorage.getItem("user");
        const token = localStorage.getItem("token");

        if (savedUser && token) {
          setUser(JSON.parse(savedUser));
        }
      } catch (error) {
        console.error("[AUTH] Init error:", error);
      } finally {
        setLoading(false);
      }
    };

    initAuth();
  }, []);

  const login = async (credentials) => {
    try {
      const { email, password } = credentials;
      const response = await authAPI.login(email, password);
      const { user: userData, access_token } = response.data;

      setUser(userData);
      localStorage.setItem("user", JSON.stringify(userData));
      localStorage.setItem("token", access_token);
      return userData;
    } catch (error) {
      console.error("Login Error:", error.response?.data || error.message);
      // Ensure the error has a clear message for the UI
      if (error.response?.data?.error) error.message = error.response.data.error;
      else if (error.response?.data?.message) error.message = error.response.data.message;
      throw error;
    }
  };

  const signup = async (userData) => {
    try {
      // Map fullName to full_name for backend if needed
      const signupData = {
        username: userData.username,
        email: userData.email,
        password: userData.password,
        full_name: userData.fullName || userData.full_name || ""
      };
      
      const response = await authAPI.signup(signupData);
      const { user: newUserData, access_token } = response.data;

      setUser(newUserData);
      localStorage.setItem("user", JSON.stringify(newUserData));
      localStorage.setItem("token", access_token);
      return newUserData;
    } catch (error) {
      console.error("Signup Error:", error.response?.data || error.message);
      if (error.response?.data?.error) error.message = error.response.data.error;
      else if (error.response?.data?.message) error.message = error.response.data.message;
      throw error;
    }
  };

  const socialLogin = async (providerName) => {
    try {
      setLoading(true);
      const provider = providerName === "google" ? googleProvider : githubProvider;

      console.log(`[AUTH] Attempting login for ${providerName}...`);
      
      // STRATEGY: Try popup first. If blocked (iframe), auto-fallback to redirect.
      try {
        const firebaseResult = await signInWithPopup(auth, provider);
        const idToken = await firebaseResult.user.getIdToken();
        const response = await authAPI.firebaseLogin(idToken);
        const { user: userData, access_token } = response.data;

        setUser(userData);
        localStorage.setItem("user", JSON.stringify(userData));
        localStorage.setItem("token", access_token);
        return userData;
      } catch (pError) {
        console.error(`[AUTH] Popup error code: ${pError.code}`, pError);
        
        if (pError.code === "auth/internal-error") {
            throw new Error("Config Error: Please ensure this domain is Authorized in Firebase Console.");
        }
        
        // AUTOMATIC FALLBACK: If popup is blocked (common in iframes like HF),
        // silently switch to redirect mode. The page will redirect to Google/GitHub,
        // then come back. The getRedirectResult() in initAuth handles the return.
        if (pError.code === "auth/popup-blocked" || pError.code === "auth/cancelled-popup-request") {
            console.warn(`[AUTH] Popup blocked! Auto-switching to REDIRECT mode for ${providerName}...`);
            toast.loading("Redirecting to login...", { duration: 3000 });
            await signInWithRedirect(auth, provider);
            return null; // Page will redirect, so we won't reach here
        }
        throw pError;
      }
    } catch (error) {
      console.error(`${providerName} login error:`, error);
      throw new Error(error.message || `${providerName} login failed`);
    } finally {
      // Don't set loading to false if redirecting
    }
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem("user");
    localStorage.removeItem("token");
  };

  const updateUser = (updatedUser) => {
    setUser(updatedUser);
    localStorage.setItem("user", JSON.stringify(updatedUser));
  };

  const refreshProfile = async () => {
    try {
      const { userAPI } = await import("../services/api");
      const response = await userAPI.getProfile();
      const userData = response.data;
      setUser(userData);
      localStorage.setItem("user", JSON.stringify(userData));
      return userData;
    } catch (error) {
      console.error("Refresh Profile Error:", error);
      throw error;
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        signup,
        socialLogin,
        logout,
        updateUser,
        refreshProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
export { AuthContext };
export default AuthContext;
