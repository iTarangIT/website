"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { Battery, LogOut, Menu } from "lucide-react";
import { clearRole, type PortalRole } from "@/lib/session";
import Badge from "@/components/ui/Badge";

interface TopBarProps {
  role: PortalRole;
  onMobileMenuClick?: () => void;
  rightSlot?: React.ReactNode;
}

const ROLE_LABEL: Record<PortalRole, string> = {
  nbfc: "NBFC",
  dealer: "Dealer",
  itarang: "iTarang Admin",
};

const ROLE_BADGE_VARIANT: Record<PortalRole, "default" | "success" | "accent"> = {
  nbfc: "default",
  dealer: "success",
  itarang: "accent",
};

export default function TopBar({ role, onMobileMenuClick, rightSlot }: TopBarProps) {
  const router = useRouter();

  const logout = () => {
    clearRole();
    router.replace("/");
  };

  return (
    <header className="flex items-center justify-between gap-4 h-14 px-4 sm:px-6 border-b border-white/10 bg-black/30 backdrop-blur-sm">
      <div className="flex items-center gap-3">
        {onMobileMenuClick && (
          <button
            onClick={onMobileMenuClick}
            className="lg:hidden p-1.5 rounded-md text-gray-400 hover:text-white hover:bg-white/5"
            aria-label="Open menu"
          >
            <Menu className="h-5 w-5" />
          </button>
        )}
        <Link href="/" className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center">
            <Battery className="h-3.5 w-3.5 text-white" />
          </div>
          <span className="text-sm font-bold text-white tracking-tight font-sans hidden sm:inline">iTarang</span>
        </Link>
        <span className="h-4 w-px bg-white/15" aria-hidden />
        <Badge variant={ROLE_BADGE_VARIANT[role]} className="text-[10px] uppercase tracking-wider">
          {ROLE_LABEL[role]}
        </Badge>
      </div>

      <div className="flex items-center gap-2">
        {rightSlot}
        <button
          onClick={logout}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md text-gray-400 hover:text-white hover:bg-white/5 transition-colors"
          title="Log out"
        >
          <LogOut className="h-3.5 w-3.5" />
          <span className="hidden sm:inline">Log out</span>
        </button>
      </div>
    </header>
  );
}
