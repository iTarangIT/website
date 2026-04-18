"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import { Info } from "lucide-react";
import { cn } from "@/lib/utils";

interface Props {
  methodology: string;
  children: ReactNode;
  label?: string;
}

export default function MethodologyTooltip({ methodology, children, label }: Props) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onDocClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onDocClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDocClick);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  return (
    <span className="relative inline-flex items-center gap-1" ref={ref}>
      {children}
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          e.preventDefault();
          setOpen((o) => !o);
        }}
        aria-label={label ? `Methodology for ${label}` : "Show methodology"}
        aria-expanded={open}
        className={cn(
          "inline-flex items-center justify-center h-4 w-4 rounded-full text-gray-500 hover:text-brand-300 hover:bg-white/10 transition-colors",
          open && "text-brand-300 bg-white/10",
        )}
      >
        <Info className="h-3 w-3" />
      </button>
      {open && (
        <span
          role="tooltip"
          className="absolute left-0 top-full mt-1 z-50 w-72 rounded-lg bg-gray-950 border border-white/10 shadow-2xl px-3 py-2.5 text-[11px] text-gray-300 leading-relaxed"
          onClick={(e) => e.stopPropagation()}
        >
          <span className="block text-[10px] uppercase tracking-wider text-gray-500 font-bold mb-1">
            Methodology
          </span>
          {methodology}
        </span>
      )}
    </span>
  );
}
