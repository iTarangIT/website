"use client";

import { MessageCircle, ArrowRight } from "lucide-react";
import { siteConfig } from "@/data/site";
import FadeInOnScroll from "@/components/shared/FadeInOnScroll";
import Button from "@/components/ui/Button";
import { GridPattern } from "@/components/ui/grid-pattern";
import { cn } from "@/lib/utils";

const roles = [
  { label: "I'm a Driver", message: "Hi, I'm a driver interested in iTarang batteries.", emoji: "🛺" },
  { label: "I'm a Dealer", message: "Hi, I'm a dealer interested in partnering with iTarang.", emoji: "🏪" },
  { label: "I'm an NBFC", message: "Hi, I represent an NBFC interested in iTarang's lending platform.", emoji: "🏦" },
  { label: "I'm an Investor", message: "Hi, I'm an investor interested in learning more about iTarang.", emoji: "📊" },
];

export default function HomeCTA() {
  const phoneNumber = siteConfig.whatsapp.replace(/[^0-9]/g, "");

  return (
    <section className="py-24 md:py-32 relative overflow-hidden">
      {/* Rich gradient background */}
      <div className="absolute inset-0 bg-gradient-to-br from-brand-950 via-brand-900 to-brand-800" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(103,61,230,0.3),transparent_60%)]" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_right,rgba(252,81,133,0.1),transparent_50%)]" />

      {/* Subtle grid */}
      <GridPattern
        width={60}
        height={60}
        className={cn(
          "fill-brand-400/3 stroke-brand-400/5",
          "[mask-image:radial-gradient(500px_circle_at_60%_40%,white,transparent)]",
        )}
      />

      <div className="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8 text-center relative z-10">
        <FadeInOnScroll>
          <h2 className="text-4xl sm:text-5xl lg:text-6xl text-white tracking-tight leading-[1.1]">
            Let&apos;s talk
          </h2>
          <p className="mt-6 text-lg text-brand-200/70 max-w-lg mx-auto">
            Pick your role and we&apos;ll connect you with the right person — instantly.
          </p>

          <div className="mt-12 grid grid-cols-2 gap-3 max-w-md mx-auto">
            {roles.map((role) => (
              <a
                key={role.label}
                href={`https://wa.me/${phoneNumber}?text=${encodeURIComponent(role.message)}`}
                target="_blank"
                rel="noopener noreferrer"
                className="group flex items-center justify-center gap-2.5 rounded-2xl bg-white/5 border border-white/10 px-4 py-4 text-sm font-medium text-white/80 hover:bg-white/15 hover:border-white/25 hover:text-white transition-all duration-300 backdrop-blur-sm"
              >
                <span className="text-lg">{role.emoji}</span>
                <span className="font-sans">{role.label}</span>
              </a>
            ))}
          </div>

          <div className="mt-10 flex items-center justify-center gap-3">
            <div className="h-px w-8 bg-white/20" />
            <span className="text-xs text-white/30 uppercase tracking-widest">or</span>
            <div className="h-px w-8 bg-white/20" />
          </div>

          <div className="mt-6">
            <Button
              href="/contact"
              size="lg"
              className="bg-white text-brand-700 hover:bg-gray-100 shadow-xl shadow-black/20"
            >
              Fill out a form
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </div>
        </FadeInOnScroll>
      </div>
    </section>
  );
}
