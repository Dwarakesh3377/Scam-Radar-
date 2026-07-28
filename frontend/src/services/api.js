import axios from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://127.0.0.1:5000/api";

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // Increased to 2 minutes for initial model loading
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor to add token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  },
);

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      console.warn("Unauthorized access - clearing session");
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      // Use location.href for a hard reload to auth page
      if (!window.location.pathname.includes('/auth')) {
        window.location.href = "/auth";
      }
    }
    return Promise.reject(error);
  },
);

export const authAPI = {
  login: (email, password) => api.post("/auth/login", { email, password }),
  signup: (userData) => api.post("/auth/register", userData),
  googleLogin: (token) => api.post("/auth/google-login", { token }),
  githubLogin: (code) => api.post("/auth/github-login", { code }),
  firebaseLogin: (idToken) => api.post("/auth/firebase-login", { idToken }),
  logout: () => api.post("/auth/logout"),
  refreshToken: () => api.post("/auth/refresh"),
  forgotPassword: (email) => api.post("/auth/forgot-password", { email }),
  resetPassword: (token, password) =>
    api.post("/auth/reset-password", { token, password }),
  updateProfile: (profileData) => api.put("/auth/profile", profileData),
};

export const analysisAPI = {
  analyze: (data) => api.post("/analyze/analyze", data),
  getHistory: (page = 1, limit = 10) =>
    api.get(`/analyze/history?page=${page}&limit=${limit}`),
  getAnalysis: (id) => api.get(`/analyze/analysis/${id}`),
  getSharedAnalysis: (id) => api.get(`/analyze/shared/${id}`),
  deleteAnalysis: (id) => api.delete(`/analyze/analysis/${id}`),
  getStats: () => api.get("/analyze/stats"),
  getDistribution: () => api.get("/analyze/distribution"),
  getTrends: () => api.get("/analyze/trends"),
  clearHistory: () => api.delete("/analyze/history"),
  bulkDelete: (ids) => api.post("/analyze/bulk-delete", { ids }),
};

export const feedbackAPI = {
  submitFeedback: (feedback) => api.post("/feedback", feedback),
  submitReview: (review) => api.post("/reviews", review),
  getReviews: (company) => api.get(`/reviews/company/${company}`),
  getMyFeedback: () => api.get("/feedback/my-feedback"),
  getNegativeReviews: () => api.get("/reviews/negative"),
};

export const userAPI = {
  getProfile: () => api.get("/auth/profile"),
  updateProfile: (profileData) => api.put("/auth/profile", profileData),
  changePassword: (passwordData) => api.put("/auth/password", passwordData),
  deleteAccount: () => api.delete("/settings/delete-account"),
  getStats: () => api.get("/auth/stats"),
};

export const settingsAPI = {
  getSettings: () => api.get("/settings"),
  updateSettings: (settings) => api.put("/settings", settings),
  getLanguages: () => api.get("/settings/languages"),
  getThemes: () => api.get("/settings/themes"),
};

export default api;
