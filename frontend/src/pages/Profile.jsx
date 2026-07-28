import React, { useContext, useEffect, useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { AuthContext } from "../context/AuthContext";
import { AnalyticsContext } from "../context/AnalyticsContext";
import { LanguageContext } from "../context/LanguageContext";
import {
  FaUser,
  FaHistory,
  FaCalendarAlt,
  FaChartBar,
  FaEnvelope,
  FaClock,
  FaCalendarPlus,
  FaEdit,
  FaTimes,
  FaCheck,
  FaPalette,
  FaUserCircle,
} from "react-icons/fa";
import "./Profile.css";

const AVATARS = [
  { id: "default", name: "Default" },
  { id: "bear", name: "Bear" },
  { id: "cheetah", name: "Cheetah" },
  { id: "cobra", name: "Cobra" },
  { id: "deer", name: "Deer" },
  { id: "dragon", name: "Dragon" },
  { id: "eagle", name: "Eagle" },
  { id: "elephant", name: "Elephant" },
  { id: "falcon", name: "Falcon" },
  { id: "fox", name: "Fox" },
  { id: "gorilla", name: "Gorilla" },
  { id: "griffin", name: "Griffin" },
  { id: "hawk", name: "Hawk" },
  { id: "hydra", name: "Hydra" },
  { id: "hyena", name: "Hyena" },
  { id: "kraken", name: "Kraken" },
  { id: "leopard", name: "Leopard" },
  { id: "lion", name: "Lion" },
  { id: "owl", name: "Owl" },
  { id: "panda", name: "Panda" },
  { id: "panther", name: "Panther" },
  { id: "pegasus", name: "Pegasus" },
  { id: "penguin", name: "Penguin" },
  { id: "phoenix", name: "Phoenix" },
  { id: "polar bear", name: "Polar Bear" },
  { id: "raven", name: "Raven" },
  { id: "rhino", name: "Rhino" },
  { id: "shark", name: "Shark" },
  { id: "snow leopard", name: "Snow Leopard" },
  { id: "Tiger", name: "Tiger" },
  { id: "wolf", name: "Wolf" },
];

const THEME_COLORS = [
  "Cyan", 
  "Blue", 
  "Purple", 
  "Indigo", 
  "Pink",
  "NeonYellow",
  "NeonGold",
  "IceBlue",
  "SlateGrey",
  "NeonSilver"
];

const Profile = () => {
  const { user, updateUser, refreshProfile } = useContext(AuthContext);
  const { userStats, getAnalysisHistory, refreshAnalytics, history } =
    useContext(AnalyticsContext);
  const { t } = useContext(LanguageContext);
  const navigate = useNavigate();

  const [lastAnalysisDate, setLastAnalysisDate] = useState("N/A");
  const [showEditModal, setShowEditModal] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);

  // Edit Form State
  const [editName, setEditName] = useState(user?.full_name || user?.name || "");
  const [editBio, setEditBio] = useState(user?.bio || "");
  const [selectedAvatar, setSelectedAvatar] = useState(
    user?.avatar_id || "1",
  );
  const [selectedColor, setSelectedColor] = useState(
    user?.theme_color || "Cyan",
  );

  useEffect(() => {
    if (!user) {
      navigate("/auth");
      return;
    }

    let isMounted = true;
    const syncData = async () => {
      setIsSyncing(true);
      try {
        await Promise.all([refreshProfile(), refreshAnalytics()]);
        const validHistory = await getAnalysisHistory();
        if (isMounted) {
          if (validHistory.length > 0) {
            const latestDate = validHistory[0]?.created_at;
            if (latestDate) {
              const latest = new Date(latestDate);
              setLastAnalysisDate(latest.toLocaleDateString());
            }
          }
        }
      } catch (error) {
        console.error("Error syncing profile data:", error);
      } finally {
        if (isMounted) setIsSyncing(false);
      }
    };
    syncData();
    return () => {
      isMounted = false;
    };
  }, [user?.email, navigate]);

  // Update edit state when user data loads
  useEffect(() => {
    if (user) {
      setEditName(user.full_name || user.name || "");
      setEditBio(user.bio || "");
      setSelectedAvatar(user.avatar_id || "1");
      setSelectedColor(user.theme_color || "Cyan");
    }
  }, [user]);

  const handleSaveProfile = async () => {
    try {
      const updatedUser = {
        ...user,
        full_name: editName,
        bio: editBio,
        avatar_id: selectedAvatar,
        theme_color: selectedColor,
      };
      await updateUser(updatedUser);
      // In a real app, you'd call your API here
      const { authAPI } = await import("../services/api");
      await authAPI.updateProfile({
        full_name: editName,
        bio: editBio,
        avatar_id: selectedAvatar,
        theme_color: selectedColor,
      });
      setShowEditModal(false);
    } catch (error) {
      console.error("Failed to update profile:", error);
    }
  };

  const getAvatarPath = (id) => `/avatars/${id}.png`;

  return (
    <div className="profile-page-root">
      <div className="profile-container premium-card">
        <div className="profile-header">
          <div className="avatar-wrapper">
            {user?.avatar_id === 'default' ? (
              <FaUserCircle 
                style={{ width: '180px', height: '180px', color: 'var(--accent-color)' }}
              />
            ) : (
              <img 
                src={`/avatars/${encodeURIComponent(user?.avatar_id || "lion")}.png`} 
                alt="Avatar"
                className="profile-avatar-img-styled"
                style={{ width: '180px', height: '180px', borderRadius: '50%', objectFit: 'cover' }}
                onError={(e) => { e.target.src = '/avatars/lion.png'; }}
              />
            )}
          </div>
          <div className="user-info-text">
            <h1 className="user-glow-name">{user?.full_name || "User"}</h1>
            <p className="user-email-text">
              <FaEnvelope /> {user?.email}
            </p>
            {user?.bio && <p className="user-bio-text">"{user.bio}"</p>}
          </div>
          <button
            className="edit-profile-btn"
            onClick={() => setShowEditModal(true)}
          >
            <FaEdit /> Edit Profile
          </button>
        </div>

        <div className="profile-stats-grid">
          <div className="stat-card clickable">
            <div className="stat-icon">
              <FaUser />
            </div>
            <div className="stat-content">
              <span className="stat-label">Account Type</span>
              <span className="stat-value">Standard User</span>
            </div>
          </div>
          <div className="stat-card clickable">
            <div className="stat-icon">
              <FaCalendarPlus />
            </div>
            <div className="stat-content">
              <span className="stat-label">Joined Date</span>
              <span className="stat-value">
                {user?.created_at
                  ? new Date(user.created_at).toLocaleDateString()
                  : "N/A"}
              </span>
            </div>
          </div>
          <div
            className="stat-card"
          >
            <div className="stat-icon">
              <FaChartBar />
            </div>
            <div className="stat-content">
              <span className="stat-label">Total Analyses</span>
              <span className="stat-value">
                {history.length || userStats?.totalAnalyses || 0}
              </span>
            </div>
          </div>
          <div className="stat-card clickable">
            <div className="stat-icon">
              <FaHistory />
            </div>
            <div className="stat-content">
              <span className="stat-label">Last Analysis Date</span>
              <span className="stat-value">
                {lastAnalysisDate === "N/A"
                  ? "No analysis yet"
                  : lastAnalysisDate}
              </span>
            </div>
          </div>
        </div>

        <div className="profile-footer">
          <button className="home-return-btn" onClick={() => navigate("/")}>
            <FaHistory /> Return to Home
          </button>
        </div>
      </div>

      {/* Edit Profile Modal */}
      {showEditModal && (
        <div className="modal-overlay">
          <div className="modal-content edit-modal">
            <div className="modal-header">
              <h2>Edit Profile</h2>
              <button
                className="close-btn"
                onClick={() => setShowEditModal(false)}
              >
                <FaTimes />
              </button>
            </div>
            <div className="modal-body">
              <div className="input-group">
                <label>Full Name</label>
                <input
                  type="text"
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                />
              </div>
              <div className="input-group">
                <label>Bio</label>
                <textarea
                  value={editBio}
                  onChange={(e) => setEditBio(e.target.value)}
                  placeholder="Tell us about yourself..."
                  rows="2"
                />
              </div>

              <label className="section-label">Choose Avatar</label>
              <div className="avatar-grid-picker">
                {AVATARS.map((avatar) => (
                  <div
                    key={avatar.id}
                    className={`avatar-choice ${selectedAvatar === avatar.id ? "active" : ""}`}
                    onClick={() => setSelectedAvatar(avatar.id)}
                    title={avatar.name}
                  >
                    <div className="avatar-choice-content">
                      {avatar.id === 'default' ? (
                        <div className="default-avatar-placeholder" style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--card-bg)', borderRadius: '12px' }}>
                          <FaUserCircle size="60%" />
                        </div>
                      ) : (
                        <img 
                          src={`/avatars/${encodeURIComponent(avatar.id)}.png`} 
                          alt={avatar.name}
                          style={{ width: '100%', height: '100%', borderRadius: '12px', objectFit: 'cover' }}
                        />
                      )}
                    </div>
                    {selectedAvatar === avatar.id && (
                      <div className="checked-badge">
                        <FaCheck />
                      </div>
                    )}
                  </div>
                ))}
              </div>

              <label className="section-label">Theme Accent Color</label>
              <div className="color-picker-strip">
                {THEME_COLORS.map((color) => (
                  <div
                    key={color}
                    className={`color-choice ${color.toLowerCase()} ${selectedColor === color ? "active" : ""}`}
                    onClick={() => setSelectedColor(color)}
                  >
                    <div className="color-circle"></div>
                    <span>{color}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="modal-footer">
              <button className="save-btn" onClick={handleSaveProfile}>
                Save Changes
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};

export default Profile;
