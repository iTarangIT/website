"use client";

import { CalendarDays, ArrowRight } from "lucide-react";
import Button from "@/components/ui/Button";
import GatedForm from "@/components/shared/GatedForm";
import FadeInOnScroll from "@/components/shared/FadeInOnScroll";

export default function InvestorCTA() {
  return (
    <section className="py-20 md:py-28 bg-gray-50">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-16 items-start">
          {/* Left column - Persuasive copy */}
          <FadeInOnScroll direction="left">
            <div>
              <span className="inline-block mb-4 px-4 py-1.5 text-xs font-semibold uppercase tracking-widest rounded-full text-brand-600 bg-brand-100">
                Let&apos;s Talk
              </span>

              <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-gray-900 mb-6">
                Let&apos;s Build This Together
              </h2>

              <p className="text-lg text-gray-600 leading-relaxed mb-6">
                iTarang is building the intelligence infrastructure for India&apos;s
                EV battery economy. We&apos;re looking for investors who understand
                that the best fintech opportunities lie at the intersection of
                data, credit, and real assets.
              </p>

              <div className="space-y-4 mb-8">
                <div className="flex items-start gap-3">
                  <div className="flex h-6 w-6 items-center justify-center rounded-full bg-accent-green/20 shrink-0 mt-0.5">
                    <ArrowRight className="h-3.5 w-3.5 text-accent-green" />
                  </div>
                  <p className="text-sm text-gray-600">
                    <span className="font-semibold text-gray-900">
                      Category-defining position
                    </span>{" "}
                    — first mover in battery-as-a-financial-asset infrastructure
                  </p>
                </div>
                <div className="flex items-start gap-3">
                  <div className="flex h-6 w-6 items-center justify-center rounded-full bg-accent-green/20 shrink-0 mt-0.5">
                    <ArrowRight className="h-3.5 w-3.5 text-accent-green" />
                  </div>
                  <p className="text-sm text-gray-600">
                    <span className="font-semibold text-gray-900">
                      Capital-efficient model
                    </span>{" "}
                    — 65-70% gross margins with compounding per-battery LTV
                  </p>
                </div>
                <div className="flex items-start gap-3">
                  <div className="flex h-6 w-6 items-center justify-center rounded-full bg-accent-green/20 shrink-0 mt-0.5">
                    <ArrowRight className="h-3.5 w-3.5 text-accent-green" />
                  </div>
                  <p className="text-sm text-gray-600">
                    <span className="font-semibold text-gray-900">
                      Regulatory tailwinds
                    </span>{" "}
                    — BWMR 2022 mandates create a structural moat for compliant
                    platforms
                  </p>
                </div>
                <div className="flex items-start gap-3">
                  <div className="flex h-6 w-6 items-center justify-center rounded-full bg-accent-green/20 shrink-0 mt-0.5">
                    <ArrowRight className="h-3.5 w-3.5 text-accent-green" />
                  </div>
                  <p className="text-sm text-gray-600">
                    <span className="font-semibold text-gray-900">
                      Clear path to Series Seed
                    </span>{" "}
                    — 12-month milestones with measurable KPIs already defined
                  </p>
                </div>
              </div>

              {/* Calendly placeholder */}
              <div className="rounded-xl bg-white border border-gray-200 p-6 shadow-sm">
                <div className="flex items-center gap-3 mb-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-50">
                    <CalendarDays className="h-5 w-5 text-brand-500" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">
                      Schedule a Founder Call
                    </h3>
                    <p className="text-xs text-gray-500">
                      30-min deep dive on the opportunity
                    </p>
                  </div>
                </div>
                <Button
                  href="https://calendly.com"
                  size="md"
                  className="w-full"
                >
                  <CalendarDays className="h-4 w-4 mr-2" />
                  Book a Time on Calendly
                </Button>
                <p className="mt-2 text-xs text-gray-400 text-center">
                  Replace with actual Calendly scheduling link
                </p>
              </div>
            </div>
          </FadeInOnScroll>

          {/* Right column - Gated Form */}
          <FadeInOnScroll direction="right" delay={0.15}>
            <div className="lg:sticky lg:top-24">
              <GatedForm
                title="Request the Full Pitch Deck"
                description="Get access to our detailed investor deck with financial projections, competitive landscape, and GTM strategy."
                downloadUrl="/iTarang-Investor-Deck.pdf"
              />
            </div>
          </FadeInOnScroll>
        </div>
      </div>
    </section>
  );
}
