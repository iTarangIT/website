"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Battery,
  FileText,
  Store,
  Package,
  ReceiptIndianRupee,
  Wrench,
  Shield,
  Phone,
  Activity,
  TrendingDown,
  Cog,
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
    { label: "Assets", href: "/nbfc/assets", icon: Battery },
    { label: "Reports", href: "/nbfc?tab=reports", icon: FileText, disabled: true },
    { label: "Settings", href: "/nbfc?tab=settings", icon: Cog, disabled: true },
  ],
  dealer: [
    { label: "Overview", href: "/dealer", icon: Store },
    { label: "Inventory", href: "/dealer?tab=inventory", icon: Package, disabled: true },
    { label: "EMI", href: "/dealer?tab=emi", icon: ReceiptIndianRupee, disabled: true },
    { label: "Service", href: "/dealer?tab=service", icon: Wrench, disabled: true },
  ],
  itarang: [
    { label: "Control Tower", href: "/itarang", icon: Shield },
    { label: "Leads", href: "/itarang/leads", icon: Phone },
    { label: "Fleet", href: "/itarang?tab=fleet", icon: Activity, disabled: true },
    { label: "Risk", href: "/itarang?tab=risk", icon: TrendingDown, disabled: true },
    { label: "Service", href: "/itarang?tab=service", icon: Wrench, disabled: true },
  ],
};

interface SidebarProps {
  role: PortalRole;
}

export default function Sidebar({ role }: SidebarProps) {
  const pathname = usePathname();
  const items = NAV[role];

  return (
    <aside className="hidden lg:flex w-60 shrink-0 flex-col border-r border-white/10 bg-black/20 backdrop-blur-sm">
      <div className="px-4 pt-6 pb-4">
        <p className="text-[10px] uppercase tracking-wider text-gray-500 font-semibold mb-3 px-2">
          {role === "nbfc" ? "NBFC Portal" : role === "dealer" ? "Dealer Portal" : "iTarang Admin"}
        </p>
        <nav className="space-y-0.5">
          {items.map((item) => {
            const isActive = !item.disabled && (pathname === item.href || (item.href !== "/nbfc" && item.href !== "/dealer" && item.href !== "/itarang" && pathname.startsWith(item.href.split("?")[0])));
            const baseHref = item.href.split("?")[0];
            const pathActive = pathname === baseHref;
            const active = isActive || pathActive;
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
                  <span className="ml-auto text-[10px] font-medium uppercase tracking-wider text-gray-600">
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
                    ? "bg-brand-500/15 text-white font-medium"
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
      <div className="mt-auto p-4 border-t border-white/10">
        <p className="text-[10px] text-gray-600 leading-relaxed px-2">
          Demo environment · Mock data · Not connected to production
        </p>
      </div>
    </aside>
  );
}
