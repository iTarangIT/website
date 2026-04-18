"use client";

import { useState, type ReactNode } from "react";
import { BarChart2, Table as TableIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface Props {
  chart: ReactNode;
  table: ReactNode;
  tableLabel?: string;
  summary?: string;
  className?: string;
}

export default function ChartWithTableFallback({ chart, table, tableLabel = "View as table", summary, className }: Props) {
  const [mode, setMode] = useState<"chart" | "table">("chart");

  return (
    <div className={className}>
      <div className="flex items-center justify-end mb-2">
        <div className="inline-flex items-center gap-0 text-[10px] rounded-md bg-white/5 border border-white/10 p-0.5">
          <button
            onClick={() => setMode("chart")}
            aria-pressed={mode === "chart"}
            className={cn(
              "inline-flex items-center gap-1 px-2 py-1 rounded-sm transition-colors",
              mode === "chart" ? "bg-brand-500 text-white" : "text-gray-400 hover:text-white",
            )}
          >
            <BarChart2 className="h-3 w-3" />
            Chart
          </button>
          <button
            onClick={() => setMode("table")}
            aria-pressed={mode === "table"}
            className={cn(
              "inline-flex items-center gap-1 px-2 py-1 rounded-sm transition-colors",
              mode === "table" ? "bg-brand-500 text-white" : "text-gray-400 hover:text-white",
            )}
          >
            <TableIcon className="h-3 w-3" />
            {tableLabel}
          </button>
        </div>
      </div>
      {mode === "chart" ? chart : table}
      {summary && <p className="text-[11px] text-gray-500 italic mt-2">{summary}</p>}
    </div>
  );
}
