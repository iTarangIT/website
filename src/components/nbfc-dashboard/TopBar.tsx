"use client";

import { Menu } from "lucide-react";
import { demoProfile } from "@/lib/nbfc-mock-data";
import { formatNumber } from "@/lib/utils";

export default function TopBar({ onOpenMobile }: { onOpenMobile: () => void }) {
  return (
    <header className="sticky top-0 z-20 bg-white/80 backdrop-blur-xl border-b border-gray-200">
      <div className="flex items-center justify-between gap-4 px-4 sm:px-6 lg:px-8 h-16">
        <div className="flex items-center gap-3 min-w-0">
          <button
            onClick={onOpenMobile}
            className="lg:hidden p-2 -ml-2 rounded-lg text-gray-500 hover:bg-gray-100"
            aria-label="Open sidebar"
          >
            <Menu className="h-5 w-5" />
          </button>
          <div className="min-w-0">
            <p className="text-[10px] font-semibold uppercase tracking-widest text-gray-400">
              Logged in as
            </p>
            <p className="text-sm font-semibold text-gray-900 truncate">
              {demoProfile.name}
            </p>
          </div>
        </div>

        <div className="hidden md:inline-flex items-center gap-3 rounded-full border border-gray-200 bg-gray-50 px-4 py-1.5 text-xs font-medium text-gray-600">
          <span>
            Total AUM{" "}
            <span className="font-semibold text-gray-900">{demoProfile.aumLabel}</span>
          </span>
          <span className="text-gray-300">·</span>
          <span>
            Active Loans{" "}
            <span className="font-semibold text-gray-900">
              {formatNumber(demoProfile.activeLoans)}
            </span>
          </span>
          <span className="text-gray-300">·</span>
          <span>
            NPA{" "}
            <span className="font-semibold text-accent-green">{demoProfile.npaPct}%</span>
          </span>
        </div>
      </div>
    </header>
  );
}
