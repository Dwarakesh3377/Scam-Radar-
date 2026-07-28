import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider, GithubAuthProvider } from "firebase/auth";

// Your web app's Firebase configuration
const firebaseConfig = {
    apiKey: "AIzaSyBzSLriZPvO3zymrSJfacSipeNZ_xnCJdk",
    authDomain: "scam-risk-detection.firebaseapp.com",
    projectId: "scam-risk-detection",
    storageBucket: "scam-risk-detection.firebasestorage.app",
    messagingSenderId: "813384314424",
    appId: "1:813384314424:web:2991037a60f763d97540cd"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

// Auth providers
const googleProvider = new GoogleAuthProvider();
googleProvider.setCustomParameters({ prompt: 'select_account' });

const githubProvider = new GithubAuthProvider();
githubProvider.setCustomParameters({ prompt: 'select_account' });

export { auth, googleProvider, githubProvider };
