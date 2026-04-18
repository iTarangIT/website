"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname, useRouter } from "next/navigation";
import { LayoutDashboard, Users, LogOut } from "lucide-react";
import { cn } from "@/lib/utils";

type Item = {
  label: string;
  href: string;
  icon: typeof LayoutDashboard;
};

const items: Item[] = [
  { label: "Overview", href: "/nbfc/dashboard", icon: LayoutDashboard },
  { label: "Leads", href: "/nbfc/dashboard/leads", icon: Users },
];

export default function Sidebar({
  mobileOpen,
  onCloseMobile,
}: {
  mobileOpen: boolean;
  onCloseMobile: () => void;
}) {
  const pathname = usePathname();
  const router = useRouter();

  const handleLogout = () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("itarang_demo_session");
    }
    router.push("/");
  };

  const content = (
    <div className="flex h-full flex-col">
      <div className="px-6 py-5 border-b border-gray-200">
        <Link href="/" className="flex items-center">
          <Image
            src="/images/logo-transparent.png"
            alt="iTarang"
            width={120}
            height={32}
            className="h-7 w-auto object-contain"
          />
        </Link>
        <p className="mt-3 text-[10px] font-semibold uppercase tracking-widest text-brand-600">
          NBFC Partner Portal
        </p>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1">
        {items.map(({ label, href, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              onClick={onCloseMobile}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                active
                  ? "bg-brand-50 text-brand-700"
                  : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
              )}
            >
              <Icon className={cn("h-4 w-4", active ? "text-brand-600" : "text-gray-400")} />
              {label}
            </Link>
          );
        })}
      </nav>

      <div className="px-3 pb-5 border-t border-gray-200 pt-3">
        <button
          onClick={handleLogout}
          className="flex w-full items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-50 hover:text-gray-900 transition-colors"
        >
          <LogOut className="h-4 w-4 text-gray-400" />
          Logout
        </button>
        <p className="mt-3 px-3 text-[10px] text-gray-400">
          Demo mode — static data only.
        </p>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop */}
      <aside className="hidden lg:flex fixed inset-y-0 left-0 w-64 bg-white border-r border-gray-200 z-30">
        {content}
      </aside>

      {/* Mobile */}
      {mobileOpen && (
        <>
          <div
            className="fixed inset-0 bg-black/40 backdrop-blur-sm z-40 lg:hidden"
            onClick={onCloseMobile}
          />
          <aside className="fixed inset-y-0 left-0 w-64 bg-white border-r border-gray-200 z-50 lg:hidden">
            {content}
          </aside>
        </>
      )}
    </>
  );
}
