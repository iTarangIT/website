"use client";

import { useEffect, useState, useSyncExternalStore } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/nbfc-dashboard/Sidebar";
import TopBar from "@/components/nbfc-dashboard/TopBar";

const SESSION_KEY = "itarang_demo_session";

function getSession(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(SESSION_KEY);
}

function subscribe(callback: () => void) {
  if (typeof window === "undefined") return () => {};
  window.addEventListener("storage", callback);
  return () => window.removeEventListener("storage", callback);
}

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const session = useSyncExternalStore(subscribe, getSession, () => null);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  const authed = session === "nbfc";

  useEffect(() => {
    // useSyncExternalStore returns the real client-side value on the first
    // client render, so any non-"nbfc" value (including null) means the
    // visitor is not signed in.
    if (session !== "nbfc") {
      router.replace("/login");
    }
  }, [session, router]);

  if (!authed) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-surface-warm">
        <div className="h-6 w-6 rounded-full border-2 border-brand-500 border-t-transparent animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-surface-warm">
      <Sidebar
        mobileOpen={mobileSidebarOpen}
        onCloseMobile={() => setMobileSidebarOpen(false)}
      />
      <div className="lg:pl-64">
        <TopBar onOpenMobile={() => setMobileSidebarOpen(true)} />
        <main className="px-4 sm:px-6 lg:px-8 py-6">{children}</main>
      </div>
    </div>
  );
}
