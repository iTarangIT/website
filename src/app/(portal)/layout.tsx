"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useRole, type PortalRole } from "@/lib/session";
import PortalShell from "@/components/portal/PortalShell";
import { ExecutiveSummaryProvider } from "@/components/portal/shared/ExecutiveSummaryToggle";

const PATH_ROLE: { prefix: string; role: PortalRole }[] = [
  { prefix: "/nbfc", role: "nbfc" },
  { prefix: "/itarang", role: "itarang" },
];

function pathRole(pathname: string): PortalRole | null {
  const match = PATH_ROLE.find((p) => pathname === p.prefix || pathname.startsWith(p.prefix + "/"));
  return match?.role ?? null;
}

export default function PortalLayout({ children }: { children: React.ReactNode }) {
  const { role, ready } = useRole();
  const pathname = usePathname();
  const router = useRouter();
  const expected = pathRole(pathname);

  useEffect(() => {
    if (!ready) return;
    if (!role) {
      router.replace("/");
      return;
    }
    if (expected && expected !== role) {
      router.replace("/");
    }
  }, [ready, role, expected, router]);

  if (!ready || !role || (expected && expected !== role)) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="h-8 w-8 rounded-full border-2 border-brand-500/30 border-t-brand-500 animate-spin" />
      </div>
    );
  }

  return (
    <ExecutiveSummaryProvider>
      <PortalShell role={role}>{children}</PortalShell>
    </ExecutiveSummaryProvider>
  );
}
