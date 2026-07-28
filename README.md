---
title: Scam Detector Radar
emoji: 🛡️
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
---

# 🛡️ Scam Radar - AI-Powered Scam Risk Detection

> **Defend yourself from job, internship, and employment scams using state-of-the-art AI technology.**

![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)
![Python](https://img.shields.io/badge/Python-3.11+-green.svg)
![React](https://img.shields.io/badge/React-19.2+-61DAFB.svg)
![ML](https://img.shields.io/badge/AI-BERT_%7C_XLM--RoBERTa-red.svg)
![License](https://img.shields.io/badge/license-MIT-yellow.svg)

[![🚀 Live Demo](https://img.shields.io/badge/🚀_Live_Demo-Visit_App-brightgreen?style=for-the-badge)](https://gopieswar-scam-detector-radar.hf.space)

## 📋 Overview

Scam Radar is a multi-modular security platform designed to identify fraudulent job postings and employment-related scams. By leveraging deep learning models (BERT & XLM-RoBERTa), the system provides real-time risk assessments for job descriptions, emails, and URLs, offering job seekers a robust layer of protection in the digital market.

---

## ✨ Key Features

### 🔍 Multi-Input Analysis
- **Content Scanner**: Paste job descriptions or email bodies for instant analysis.
- **URL Check**: Verify the legitimacy of job portals and hiring links.
- **Company Lookup**: Automatically cross-reference against known scam entities.

### 🧠 Advanced AI Engine
- **Dual-Model Inference**: High accuracy using BERT (English) and XLM-RoBERTa (Cross-lingual).
- **Explainable Results**: Line-by-line red flags and risk indicators with clear explanations.
- **Visual Risk Gauge**: Real-time speedometer visualizing risk levels (Legitimate, Suspicious, Scam).

### 🌍 Global & Accessible
- **Multilingual Support**: Fully localized in 11 languages (English, Tamil, Hindi, French, Spanish, German, Japanese, Chinese, Russian, Korean, etc.).
- **Theme-Aware UI**: Premium dark/light modes with neon accent color synchronization.
- **Responsive Design**: Works seamlessly across desktops and mobile browsers.

### 🛡️ Secure & Accurate
- **Negative Review Integration**: Cross-checks companies against a database of verified victim complaints.
- **Secure Auth**: JWT-protected accounts with email normalization for consistent cross-device syncing.
- **History Tracking**: unified, real-time analysis history across Dashboard and Profile views.

---

## 🚀 Quick Start

### 1. Prerequisites
- **Python 3.11+**
- **Node.js 18+**
- **MongoDB Atlas** (Cloud or Local instance)

### 2. Configuration
Create a `.env` file in the root directory (refer to `.env.example`):
```env
MONGO_URI=your_mongodb_connection_string
JWT_SECRET_KEY=your_secret_key
FIREBASE_CONFIG={...}
```

### 3. Execution (Unified Runner)
Use the included `run.py` script to manage the entire ecosystem:

```bash
# 📦 Install all dependencies
python run.py --install

# 🚀 Run both Backend + Frontend
python run.py --both

# 🧪 Run Backend tests
python run.py --test-backend
```

### 4. Access Ports
- **Frontend UI**: [http://localhost:5173](http://localhost:5173)
- **Backend API**: [http://localhost:5000/api](http://localhost:5000/api)

---

## 📂 Project Structure

```bash
├── backend/            # Flask API, JWT Auth & Security Middlewares
├── frontend/           # React 19 + Vite (Modern Glassmorphism UI)
├── ml_models/          # Pre-trained BERT & XLM-R Model Artifacts
├── scripts/            # Database initialization and maintenance
├── run.py              # Unified CLI management script (Entry Point)
├── health_check.py     # System integrity verification tool
└── Dockerfile          # Containerization for deployment
```

---

## 🔌 API Reference (Selective)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/analyze/analyze` | Predict scam probability for content |
| `GET` | `/api/analyze/history` | Retrieve personal scan history |
| `GET` | `/api/analyze/stats` | Unified dashboard statistics |
| `DELETE` | `/api/analyze/analysis/:id` | Immediate removal of history records |
| `POST` | `/api/auth/register` | Secure registration with email normalization |

---

## 🛠️ Development & Utilities
The root directory contains several utility scripts for maintenance:
- `create_test_doc.py`: Generates formatted documentation for testing.
- `health_check.py`: Verifies MongoDB and Model connectivity.
- `verify_fix_final.py`: Comprehensive integrity check for the analysis pipeline.

---

## Troubleshooting

### Social Authentication (Google/GitHub)
If social authentication is not working on your Hugging Face Space, it is likely because the space domain is not authorized in your Firebase project.

**To fix this:**
1. Go to the [Firebase Console](https://console.firebase.google.com/).
2. Select your project.
3. Navigate to **Authentication** > **Settings** > **Authorized Domains**.
4. Click **Add Domain**.
5. Add the domain for your Hugging Face space (e.g., `gopieswar-scam-detector-radar.hf.space`).
6. Try logging in again from the space URL.

### Models Not Loading
The models are downloaded from the Hugging Face Hub at runtime. Ensure your backend has internet access and the `HF_TOKEN` (if using a private repo) is set correctly in the space settings.

---

## 📄 License
Distributed under the MIT License. See `LICENSE` for more information.

---

**🛡️ Scam Radar - Building a safer path for every job seeker.**
