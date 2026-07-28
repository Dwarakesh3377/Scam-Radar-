import React, { useEffect, useState } from 'react';
import './RiskGauge.css';

const RiskGauge = ({ percentage = 0, size = 280 }) => {
  const [animatedPercentage, setAnimatedPercentage] = useState(0);
  
  // Animate the percentage on mount
  useEffect(() => {
    const timer = setTimeout(() => {
      setAnimatedPercentage(percentage);
    }, 100);
    return () => clearTimeout(timer);
  }, [percentage]);

  // Determine color based on percentage
  let color;
  if (percentage <= 30) {
    color = '#00ff6a';
  } else if (percentage <= 60) {
    color = '#ffa500';
  } else {
    color = '#ff3e3e';
  }

  // Calculate pointer rotation (0% = -90deg, 100% = 90deg for half circle)
  const rotation = -90 + (animatedPercentage * 1.8);

  return (
    <div className="risk-gauge-container">
      <div className="gauge-wrapper" style={{ width: size, height: size * 0.7 }}>
        {/* SVG Gauge */}
        <svg viewBox="0 0 200 120" className="gauge-svg">
          <defs>
            <linearGradient id="greenGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#00ff6a" />
              <stop offset="100%" stopColor="#00cc55" />
            </linearGradient>
            <linearGradient id="orangeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#ffa500" />
              <stop offset="100%" stopColor="#ff8c00" />
            </linearGradient>
            <linearGradient id="redGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#ff4444" />
              <stop offset="100%" stopColor="#ff3e3e" />
            </linearGradient>
            <filter id="glow">
              <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
              <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
          </defs>

          {/* Gauge background track */}
          <path
            d="M 20 100 A 80 80 0 0 1 180 100"
            fill="none"
            stroke="var(--border-color)"
            strokeWidth="12"
            strokeLinecap="round"
          />

          {/* Green zone (0-33%) */}
          <path
            d="M 20 100 A 80 80 0 0 1 60 30.72"
            fill="none"
            stroke="url(#greenGradient)"
            strokeWidth="12"
            strokeLinecap="round"
            opacity="0.9"
          />

          {/* Orange zone (34-66%) */}
          <path
            d="M 60 30.72 A 80 80 0 0 1 140 30.72"
            fill="none"
            stroke="url(#orangeGradient)"
            strokeWidth="12"
            strokeLinecap="butt"
            opacity="0.9"
          />

          {/* Red zone (67-100%) */}
          <path
            d="M 140 30.72 A 80 80 0 0 1 180 100"
            fill="none"
            stroke="url(#redGradient)"
            strokeWidth="12"
            strokeLinecap="round"
            opacity="0.9"
          />

          {/* Tick marks */}
          {[0, 25, 50, 75, 100].map((tick) => {
            const angle = -180 + (tick * 1.8);
            const radians = (angle * Math.PI) / 180;
            const innerRadius = 70;
            const outerRadius = 82;
            const x1 = 100 + innerRadius * Math.cos(radians);
            const y1 = 100 + innerRadius * Math.sin(radians);
            const x2 = 100 + outerRadius * Math.cos(radians);
            const y2 = 100 + outerRadius * Math.sin(radians);
            
            return (
              <line
                key={tick}
                x1={x1}
                y1={y1}
                x2={x2}
                y2={y2}
                stroke="var(--text-secondary)"
                strokeWidth="2"
              />
            );
          })}

          {/* Pointer/Needle */}
          <g 
            transform={`rotate(${rotation} 100 100)`}
            style={{ transition: 'transform 1.5s cubic-bezier(0.34, 1.56, 0.64, 1)' }}
          >
            <polygon
              points="100,25 96,100 104,100"
              fill={color}
              style={{ filter: `drop-shadow(0 0 8px ${color})` }}
            />
            <circle
              cx="100"
              cy="100"
              r="10"
              fill="var(--bg-secondary)"
              stroke={color}
              strokeWidth="2"
            />
            <circle
              cx="100"
              cy="100"
              r="4"
              fill={color}
            />
          </g>
        </svg>
      </div>
    </div>
  );
};

export default RiskGauge;