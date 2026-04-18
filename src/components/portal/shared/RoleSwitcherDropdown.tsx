"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { ChevronDown, ShieldCheck, Settings2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { setRole, ROLE_HOME, type PortalRole } from "@/lib/session";

interface Props {
  currentRole: PortalRole;
}

const ROLE_OPTIONS: { id: PortalRole; label: string; icon: typeof ShieldCheck; sub: string }[] = [
  { id: "nbfc", label: "NBFC Risk Manager", icon: ShieldCheck, sub: "Portfolio · Risk · Recovery" },
  { id: "itarang", label: "iTarang Platform Admin", icon: Settings2, sub: "Ecosystem · Auctions · Rules" },
];

export default function RoleSwitcherDropdown({ currentRole }: Props) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const router = useRouter();

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

  const pick = (role: PortalRole) => {
    setOpen(false);
    if (role === currentRole) return;
    setRole(role);
    router.push(ROLE_HOME[role]);
  };

  const current = ROLE_OPTIONS.find((r) => r.id === currentRole)!;

  return (
    <div className="relative hidden md:block" ref={ref}>
      <button
        onClick={() => setOpen((o) => !o)}
        aria-haspopup="menu"
        aria-expanded={open}
        className="inline-flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium rounded-md text-gray-300 hover:text-white hover:bg-white/5 border border-white/10"
      >
        <span className="text-gray-500">Viewing as:</span>
        <span className="text-white font-semibold">{current.label}</span>
        <ChevronDown className={cn("h-3 w-3 transition-transform", open && "rotate-180")} />
      </button>

      {open && (
        <div
          role="menu"
          className="absolute right-0 mt-2 w-72 rounded-lg bg-gray-950 border border-white/10 shadow-2xl overflow-hidden z-50"
        >
          <p className="px-3 py-2 text-[10px] uppercase tracking-wider text-gray-500 font-bold border-b border-white/5">
            Switch role
          </p>
          {ROLE_OPTIONS.map((r) => {
            const Icon = r.icon;
            const isCurrent = r.id === currentRole;
            return (
              <button
                key={r.id}
                role="menuitem"
                onClick={() => pick(r.id)}
                disabled={isCurrent}
                className={cn(
                  "w-full flex items-center gap-3 px-3 py-2.5 text-left transition-colors",
                  isCurrent ? "bg-brand-500/15 cursor-default" : "hover:bg-white/5",
                )}
              >
                <Icon className={cn("h-4 w-4 shrink-0", isCurrent ? "text-brand-200" : "text-gray-400")} />
                <div className="min-w-0 flex-1">
                  <p className={cn("text-xs font-semibold", isCurrent ? "text-white" : "text-gray-200")}>{r.label}</p>
                  <p className="text-[10px] text-gray-500">{r.sub}</p>
                </div>
                {isCurrent && (
                  <span className="text-[9px] uppercase tracking-wider text-brand-200 font-bold">Current</span>
                )}
              </button>
            );
          })}
          <p className="px-3 py-2 text-[10px] text-gray-500 border-t border-white/5 bg-black/20">
            Switching the role updates the session and redirects to the other workspace.
          </p>
        </div>
      )}
    </div>
  );
}
