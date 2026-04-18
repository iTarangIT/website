"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { Battery, LogOut, Bell } from "lucide-react";
import { clearRole, type PortalRole } from "@/lib/session";
import Badge from "@/components/ui/Badge";

interface TopBarProps {
  role: PortalRole;
  rightSlot?: React.ReactNode;
}

const ROLE_LABEL: Record<PortalRole, string> = {
  nbfc: "NBFC Risk Manager",
  itarang: "iTarang Platform Admin",
};

const ROLE_USER: Record<PortalRole, string> = {
  nbfc: "Priya Sharma",
  itarang: "Rohit Jain",
};

export default function TopBar({ role, rightSlot }: TopBarProps) {
  const router = useRouter();

  const logout = () => {
    clearRole();
    router.replace("/");
  };

  return (
    <header className="flex items-center justify-between gap-4 h-14 px-4 sm:px-6 border-b border-white/10 bg-black/30 backdrop-blur-sm">
      <div className="flex items-center gap-3 min-w-0">
        <Link href="/" className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center">
            <Battery className="h-3.5 w-3.5 text-white" />
          </div>
          <span className="text-sm font-bold text-white tracking-tight font-sans hidden sm:inline">
            iTarang NBFC Intelligence
          </span>
        </Link>

        <span className="h-4 w-px bg-white/15" aria-hidden />

        <Badge variant="warning" className="text-[10px] uppercase tracking-wider">
          Demo Environment
        </Badge>

        <span className="h-4 w-px bg-white/15 hidden md:block" aria-hidden />

        <span className="hidden md:inline text-xs text-gray-400">
          Viewing as: <span className="text-white font-medium">{ROLE_LABEL[role]}</span>
        </span>
      </div>

      <div className="flex items-center gap-2">
        {rightSlot}

        <button
          className="relative p-1.5 rounded-md text-gray-400 hover:text-white hover:bg-white/5"
          aria-label="Notifications"
          type="button"
        >
          <Bell className="h-4 w-4" />
          <span className="absolute top-0.5 right-0.5 h-1.5 w-1.5 rounded-full bg-red-400" />
        </button>

        <div className="hidden sm:flex items-center gap-2 text-xs">
          <div className="h-7 w-7 rounded-full bg-brand-500/30 border border-brand-500/50 flex items-center justify-center text-[10px] font-bold text-brand-100">
            {ROLE_USER[role]
              .split(" ")
              .map((p) => p[0])
              .join("")}
          </div>
          <span className="text-gray-300">{ROLE_USER[role]}</span>
        </div>

        <button
          onClick={logout}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md text-gray-400 hover:text-white hover:bg-white/5 transition-colors"
          title="Log out"
          type="button"
        >
          <LogOut className="h-3.5 w-3.5" />
          <span className="hidden sm:inline">Log out</span>
        </button>
      </div>
    </header>
  );
}
