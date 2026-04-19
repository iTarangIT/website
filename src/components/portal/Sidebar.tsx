"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Megaphone,
  Brain,
  Battery,
  Recycle,
  ScrollText,
  Cog,
  UserPlus,
  BarChart3,
  Gavel,
  Package,
  Bell,
  SlidersHorizontal,
  LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { PortalRole } from "@/lib/session";

interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
  disabled?: boolean;
}

const NAV: Record<PortalRole, NavItem[]> = {
  nbfc: [
    { label: "Overview", href: "/nbfc", icon: LayoutDashboard },
    { label: "Risk Intelligence", href: "/nbfc/risk", icon: Brain },
    { label: "Battery Monitoring", href: "/nbfc/batteries", icon: Battery },
    { label: "Recovery & Auction", href: "/nbfc/recovery", icon: Recycle },
    { label: "Audit Log", href: "/nbfc/audit", icon: ScrollText },
    { label: "Settings", href: "/nbfc/settings", icon: Cog },
  ],
  itarang: [
    { label: "Ecosystem Overview", href: "/itarang", icon: LayoutDashboard },
    { label: "Partner Network", href: "/itarang/network", icon: UserPlus },
    { label: "NBFC Portfolio", href: "/itarang/monitoring", icon: BarChart3, disabled: true },
    { label: "Auction Control", href: "/itarang/auction", icon: Gavel },
    { label: "Inventory", href: "/itarang/inventory", icon: Package },
    { label: "Alerts Config", href: "/itarang/alerts", icon: Bell },
    { label: "Risk Rule Engine", href: "/itarang/risk-engine", icon: SlidersHorizontal },
    { label: "Audit Log", href: "/itarang/audit", icon: ScrollText },
  ],
};

interface SidebarProps {
  role: PortalRole;
}

const ROLE_LABEL: Record<PortalRole, { heading: string; subheading: string }> = {
  nbfc: { heading: "NBFC Intelligence", subheading: "Risk Manager · Kosh Lending" },
  itarang: { heading: "Platform Admin", subheading: "iTarang · Ecosystem Control" },
};

export default function Sidebar({ role }: SidebarProps) {
  const pathname = usePathname();
  const items = NAV[role];
  const meta = ROLE_LABEL[role];

  return (
    <aside className="hidden lg:flex w-64 shrink-0 flex-col border-r border-white/10 bg-black/20 backdrop-blur-sm">
      <div className="px-4 pt-6 pb-4">
        <p className="text-[11px] uppercase tracking-wider text-gray-500 font-bold">{meta.heading}</p>
        <p className="text-[10px] text-gray-600 mb-4">{meta.subheading}</p>
        <nav className="space-y-0.5">
          {items.map((item) => {
            const baseHref = item.href.split("?")[0];
            const active =
              pathname === baseHref ||
              (baseHref !== "/nbfc" && baseHref !== "/itarang" && pathname.startsWith(baseHref + "/"));
            const Icon = item.icon;

            if (item.disabled) {
              return (
                <span
                  key={item.href}
                  className="flex items-center gap-3 px-3 py-2 text-sm rounded-lg text-gray-500 cursor-not-allowed opacity-60"
                  aria-disabled
                >
                  <Icon className="h-4 w-4" />
                  <span>{item.label}</span>
                  <span className="ml-auto text-[10px] font-semibold uppercase tracking-wider text-gray-600">
                    soon
                  </span>
                </span>
              );
            }

            return (
              <Link
                key={item.href}
                href={baseHref}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 text-sm rounded-lg transition-colors",
                  active
                    ? "bg-brand-500/15 text-white font-semibold border border-brand-500/30"
                    : "text-gray-400 hover:text-white hover:bg-white/5",
                )}
              >
                <Icon className="h-4 w-4" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </div>
      <div className="mt-auto p-4 border-t border-white/10 space-y-1" role="status" aria-live="polite">
        <p className="text-[10px] text-gray-600 leading-relaxed">Last data sync: Today, 6:00 AM IST</p>
        <p className="text-[10px] text-accent-green leading-relaxed flex items-center gap-1">
          <span className="h-1.5 w-1.5 rounded-full bg-accent-green animate-pulse" />
          System status · operational
        </p>
      </div>
    </aside>
  );
}
