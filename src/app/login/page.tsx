"use client";

import { useRouter } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { Building2, ArrowRight, ShieldCheck } from "lucide-react";
import Button from "@/components/ui/Button";
import { demoProfile } from "@/lib/nbfc-mock-data";

export default function LoginPage() {
  const router = useRouter();

  const handleDemoLogin = () => {
    // TODO: replace with real auth before production
    if (typeof window !== "undefined") {
      localStorage.setItem("itarang_demo_session", "nbfc");
    }
    router.push("/nbfc/dashboard");
  };

  return (
    <main className="min-h-screen flex items-center justify-center relative overflow-hidden bg-brand-950 px-4 py-12">
      {/* Ambient background */}
      <div className="absolute inset-0 bg-gradient-to-br from-brand-950 via-brand-900 to-brand-800" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_left,rgba(30,163,212,0.25),transparent_55%)]" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_right,rgba(245,158,11,0.12),transparent_55%)]" />

      <div className="relative z-10 w-full max-w-md">
        <Link href="/" className="flex justify-center mb-8">
          <Image
            src="/images/logo-transparent.png"
            alt="iTarang"
            width={160}
            height={48}
            className="h-10 w-auto object-contain"
            priority
          />
        </Link>

        <div className="rounded-2xl bg-white shadow-2xl border border-white/10 p-6 sm:p-8">
          <div className="text-center mb-6">
            <div className="inline-flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-widest text-brand-600 bg-brand-50 px-3 py-1 rounded-full">
              <ShieldCheck className="h-3 w-3" />
              Partner Sign-in
            </div>
            <h1 className="mt-4 text-2xl font-semibold text-gray-900">
              Welcome back
            </h1>
            <p className="mt-1.5 text-sm text-gray-500">
              Access your iTarang NBFC partner dashboard.
            </p>
          </div>

          <div className="rounded-xl border border-gray-200 bg-gray-50 p-4 flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-brand-100 text-brand-600 shrink-0">
              <Building2 className="h-5 w-5" />
            </div>
            <div className="min-w-0">
              <p className="text-sm font-semibold text-gray-900 truncate">{demoProfile.name}</p>
              <p className="text-xs text-gray-500 truncate">{demoProfile.tagline}</p>
            </div>
          </div>

          <Button
            onClick={handleDemoLogin}
            variant="primary"
            size="lg"
            className="mt-5 w-full justify-center gap-2"
          >
            Login as Demo NBFC
            <ArrowRight className="h-4 w-4" />
          </Button>

          <p className="mt-4 text-center text-xs text-gray-400">
            Demo mode — static data only.
          </p>
        </div>

        <div className="mt-6 text-center">
          <Link
            href="/"
            className="text-xs text-white/60 hover:text-white transition-colors"
          >
            ← Back to iTarang.com
          </Link>
        </div>
      </div>
    </main>
  );
}
