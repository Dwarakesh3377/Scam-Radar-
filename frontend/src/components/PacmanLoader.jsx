import React from 'react';
import './PacmanLoader.css';

const PacmanLoader = () => {
    return (
        <div className="pacman-loader-container">
            <div className="pacman-loader">
                <div className="pacman">
                    <div className="pacman-top"></div>
                    <div className="pacman-bottom"></div>
                </div>
                <div className="dots">
                    {[...Array(4)].map((_, i) => (
                        <div 
                            key={i} 
                            className="dot"
                        ></div>
                    ))}
                </div>
            </div>
            
            <div className="analyzing-text-container">
                {"Analyzing...".split("").map((char, i) => (
                    <span key={i} className="wave-char" style={{ animationDelay: `${i * 0.1}s` }}>
                        {char}
                    </span>
                ))}
            </div>

            <p className="loading-text-static">Wait for a while until the result displays</p>
        </div>
    );
};

export default PacmanLoader;