"use client";

import { cn } from "@/lib/utils";

interface ProductPlaceholderProps {
  type: "battery" | "inverter" | "charger";
  className?: string;
}

export default function ProductPlaceholder({ type, className }: ProductPlaceholderProps) {
  return (
    <div
      className={cn(
        "relative flex items-center justify-center rounded-2xl bg-gradient-to-br from-brand-900 to-brand-800 overflow-hidden",
        className
      )}
    >
      {/* Subtle glow */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(19,143,198,0.15)_0%,transparent_70%)]" />

      <svg
        viewBox="0 0 120 120"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="relative z-10 w-2/3 h-2/3 opacity-30"
      >
        {type === "battery" && (
          <>
            <rect x="25" y="30" width="70" height="70" rx="8" stroke="currentColor" strokeWidth="2" className="text-brand-300" />
            <rect x="45" y="20" width="30" height="14" rx="4" stroke="currentColor" strokeWidth="2" className="text-brand-300" />
            <rect x="35" y="50" width="50" height="8" rx="2" fill="currentColor" className="text-brand-400/40" />
            <rect x="35" y="66" width="35" height="8" rx="2" fill="currentColor" className="text-brand-400/30" />
            <rect x="35" y="82" width="20" height="8" rx="2" fill="currentColor" className="text-brand-400/20" />
          </>
        )}
        {type === "inverter" && (
          <>
            <rect x="20" y="30" width="80" height="60" rx="8" stroke="currentColor" strokeWidth="2" className="text-brand-300" />
            {/* AC wave symbol */}
            <path d="M35 60 Q45 40 55 60 Q65 80 75 60" stroke="currentColor" strokeWidth="2.5" fill="none" className="text-brand-400" />
            {/* Vents */}
            <line x1="30" y1="78" x2="50" y2="78" stroke="currentColor" strokeWidth="1" className="text-brand-400/30" />
            <line x1="30" y1="82" x2="50" y2="82" stroke="currentColor" strokeWidth="1" className="text-brand-400/30" />
            {/* Power indicator */}
            <circle cx="85" cy="42" r="4" fill="currentColor" className="text-accent-green/50" />
          </>
        )}
        {type === "charger" && (
          <>
            <rect x="30" y="25" width="60" height="75" rx="8" stroke="currentColor" strokeWidth="2" className="text-brand-300" />
            {/* Lightning bolt */}
            <path d="M55 40 L48 58 H57 L50 80" stroke="currentColor" strokeWidth="2.5" fill="none" strokeLinecap="round" strokeLinejoin="round" className="text-brand-400" />
            {/* Cable */}
            <path d="M60 100 Q60 105 55 108 Q50 111 50 116" stroke="currentColor" strokeWidth="2" fill="none" className="text-brand-400/40" />
            {/* LED dots */}
            <circle cx="42" cy="35" r="2" fill="currentColor" className="text-accent-green/40" />
            <circle cx="50" cy="35" r="2" fill="currentColor" className="text-brand-400/30" />
            <circle cx="58" cy="35" r="2" fill="currentColor" className="text-brand-400/20" />
          </>
        )}
      </svg>
    </div>
  );
}
