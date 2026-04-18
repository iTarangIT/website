"use client";

import Sidebar from "./Sidebar";
import TopBar from "./TopBar";
import type { PortalRole } from "@/lib/session";

interface PortalShellProps {
  role: PortalRole;
  children: React.ReactNode;
  topBarRight?: React.ReactNode;
}

export default function PortalShell({ role, children, topBarRight }: PortalShellProps) {
  return (
    <div className="min-h-screen bg-gray-950 text-white flex flex-col">
      <TopBar role={role} rightSlot={topBarRight} />
      <div className="flex-1 flex min-h-0">
        <Sidebar role={role} />
        <main className="flex-1 overflow-y-auto">{children}</main>
      </div>
    </div>
  );
}
