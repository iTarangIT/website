"use client";

import { createContext, useContext, useState, type ReactNode } from "react";
import { Eye, EyeOff } from "lucide-react";
import { cn } from "@/lib/utils";

interface Ctx {
  executiveMode: boolean;
  setExecutiveMode: (v: boolean) => void;
}

const ExecCtx = createContext<Ctx>({ executiveMode: false, setExecutiveMode: () => {} });

export function ExecutiveSummaryProvider({ children }: { children: ReactNode }) {
  const [executiveMode, setExecutiveMode] = useState(false);
  return <ExecCtx.Provider value={{ executiveMode, setExecutiveMode }}>{children}</ExecCtx.Provider>;
}

export function useExecutiveMode() {
  return useContext(ExecCtx);
}

export default function ExecutiveSummaryToggle() {
  const { executiveMode, setExecutiveMode } = useExecutiveMode();
  return (
    <button
      onClick={() => setExecutiveMode(!executiveMode)}
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-1.5 text-[11px] font-medium rounded-md border transition-colors",
        executiveMode
          ? "bg-accent-green/15 border-accent-green/30 text-accent-green"
          : "bg-white/5 border-white/10 text-gray-400 hover:text-white hover:bg-white/10",
      )}
      title={executiveMode ? "Show operator detail" : "Collapse to investor summary"}
      type="button"
    >
      {executiveMode ? <Eye className="h-3 w-3" /> : <EyeOff className="h-3 w-3" />}
      Executive summary {executiveMode ? "on" : "off"}
    </button>
  );
}
