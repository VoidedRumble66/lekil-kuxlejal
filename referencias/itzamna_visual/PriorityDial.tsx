import React, { useRef } from 'react';

interface PriorityDialProps {
  value: number;
  onChange: (v: number) => void;
  size: number;
  color?: string;
  disabled?: boolean;
}

export function PriorityDial({ value, onChange, size, color = '#6366f1', disabled = false }: PriorityDialProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const center = size / 2;
  const radius = size / 2 - 8;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - value * circumference;

  const updateValue = (e: React.PointerEvent) => {
    if (disabled || !svgRef.current) return;
    const rect = svgRef.current.getBoundingClientRect();
    const cx = rect.left + center;
    const cy = rect.top + center;
    const dx = e.clientX - cx;
    const dy = e.clientY - cy;
    
    let angle = Math.atan2(dy, dx) + Math.PI / 2;
    if (angle < 0) angle += 2 * Math.PI;
    
    let pct = angle / (2 * Math.PI);
    pct = Math.max(0.01, Math.min(1, pct));
    onChange(pct);
  };

  const handlePointerDown = (e: React.PointerEvent<SVGCircleElement>) => {
    if (disabled) return;
    e.stopPropagation();
    e.currentTarget.setPointerCapture(e.pointerId);
    updateValue(e);
  };

  const handlePointerMove = (e: React.PointerEvent<SVGCircleElement>) => {
    if (disabled) return;
    if (e.buttons === 1) {
      e.stopPropagation();
      updateValue(e);
    }
  };

  const handlePointerUp = (e: React.PointerEvent<SVGCircleElement>) => {
    if (disabled) return;
    e.stopPropagation();
    try {
      e.currentTarget.releasePointerCapture(e.pointerId);
    } catch { }
  };

  return (
    <svg 
      ref={svgRef}
      width={size} 
      height={size} 
      className={`absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-20 pointer-events-none ${disabled ? '' : 'cursor-pointer'}`}
    >
      <circle 
        cx={center} cy={center} r={radius} 
        fill="transparent" 
        stroke="rgba(255,255,255,0.1)" 
        strokeWidth="6"
        className={disabled ? '' : 'pointer-events-auto'}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
      />
      <circle 
        cx={center} cy={center} r={radius} 
        fill="transparent" 
        stroke={color}
        strokeWidth="6" 
        strokeLinecap="round"
        strokeDasharray={circumference}
        strokeDashoffset={strokeDashoffset}
        transform={`rotate(-90 ${center} ${center})`}
        className="pointer-events-none transition-all duration-75"
      />
      {!disabled && (
        <circle
          cx={center + radius * Math.sin(value * 2 * Math.PI)}
          cy={center - radius * Math.cos(value * 2 * Math.PI)}
          r="6"
          fill={color}
          stroke="#0f172a"
          strokeWidth="3"
          className="pointer-events-auto shadow-sm cursor-grab active:cursor-grabbing hover:stroke-white transition-colors"
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
        />
      )}
    </svg>
  );
}
