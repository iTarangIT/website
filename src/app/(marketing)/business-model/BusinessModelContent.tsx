"use client";

import { revenueStreams, unitEconomicsBreakdown } from "@/data/revenue-streams";
import { cn } from "@/lib/utils";
import SectionHeading from "@/components/shared/SectionHeading";
import FadeInOnScroll from "@/components/shared/FadeInOnScroll";
import CTASection from "@/components/shared/CTASection";
import { Card, CardContent } from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import {
  FileCheck,
  Activity,
  Wallet,
  Recycle,
  ArrowRight,
  TrendingUp,
  ArrowDown,
} from "lucide-react";

const iconMap: Record<string, typeof FileCheck> = {
  FileCheck,
  Activity,
  Wallet,
  Recycle,
};

const natureColors: Record<string, string> = {
  "Cash Flow Engine": "bg-green-100 text-green-700",
  "High Margin ARR": "bg-brand-100 text-brand-700",
  "Volume Upside": "bg-yellow-100 text-yellow-800",
  "Regulatory Moat": "bg-purple-100 text-purple-700",
};

export default function BusinessModelContent() {
  return (
    <>
      {/* Hero */}
      <section className="relative overflow-hidden bg-brand-900 py-20 md:py-28">
        <div
          className="absolute inset-0 opacity-10"
          style={{
            backgroundImage:
              "radial-gradient(circle at 1px 1px, rgba(255,255,255,0.15) 1px, transparent 0)",
            backgroundSize: "40px 40px",
          }}
        />
        <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <FadeInOnScroll>
            <SectionHeading
              badge="Revenue Architecture"
              title="Business Model & Unit Economics"
              subtitle="A fee-based Technology Service Provider model with four diversified revenue streams, targeting 65-70% gross margins across the battery lifecycle."
              dark
            />
          </FadeInOnScroll>
        </div>
      </section>

      {/* Revenue Streams */}
      <section className="py-20 md:py-28 bg-white">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <FadeInOnScroll>
            <SectionHeading
              badge="4 Revenue Streams"
              title="Diversified, Compounding Revenue"
              subtitle="Each stream activates at a different lifecycle stage, creating a compounding revenue engine per battery."
            />
          </FadeInOnScroll>

          <div className="grid gap-6 sm:grid-cols-2">
            {revenueStreams.map((stream, idx) => {
              const Icon = iconMap[stream.icon] || FileCheck;
              return (
                <FadeInOnScroll key={stream.name} delay={idx * 0.1}>
                  <Card className="h-full hover:shadow-md transition-shadow">
                    <CardContent>
                      <div className="flex items-start gap-4">
                        <div className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-xl bg-brand-100">
                          <Icon className="h-6 w-6 text-brand-600" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex flex-wrap items-center gap-2 mb-2">
                            <h3 className="text-lg font-bold text-gray-900">
                              {stream.name}
                            </h3>
                          </div>
                          <p className="text-sm text-gray-600 mb-3">
                            {stream.description}
                          </p>
                          <div className="flex flex-wrap items-center gap-2 mb-3">
                            <Badge variant="default">{stream.phase}</Badge>
                            <span
                              className={cn(
                                "inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold",
                                natureColors[stream.nature] ||
                                  "bg-gray-100 text-gray-700"
                              )}
                            >
                              {stream.nature}
                            </span>
                          </div>
                          <div className="rounded-lg bg-gray-50 px-4 py-3">
                            <p className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-0.5">
                              Unit Economics
                            </p>
                            <p className="text-sm font-bold text-brand-700">
                              {stream.unitEconomics}
                            </p>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </FadeInOnScroll>
              );
            })}
          </div>
        </div>
      </section>

      {/* Unit Economics Breakdown */}
      <section className="py-20 md:py-28 bg-gray-50">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <FadeInOnScroll>
            <SectionHeading
              badge="Unit Economics"
              title="LTV vs CAC Breakdown"
              subtitle="Per-battery lifetime economics showing strong unit-level profitability."
            />
          </FadeInOnScroll>

          <div className="grid gap-8 lg:grid-cols-3 items-start">
            {/* Revenue Column */}
            <FadeInOnScroll direction="left">
              <Card className="border-green-200 bg-green-50/50">
                <CardContent>
                  <div className="flex items-center gap-2 mb-6">
                    <TrendingUp className="h-5 w-5 text-green-600" />
                    <h3 className="text-lg font-bold text-green-800">
                      Lifetime Revenue (LTV)
                    </h3>
                  </div>
                  <div className="space-y-4">
                    {unitEconomicsBreakdown.revenue.map((item, idx) => (
                      <div
                        key={idx}
                        className="rounded-lg bg-white p-4 border border-green-100"
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-semibold text-gray-900">
                            {item.label}
                          </span>
                          <span className="text-sm font-bold text-green-700">
                            {"amount" in item && item.amount !== undefined
                              ? `₹${item.amount.toLocaleString("en-IN")}`
                              : "amountRange" in item
                                ? (item as { amountRange: string }).amountRange
                                : ""}
                          </span>
                        </div>
                        <p className="text-xs text-gray-500">{item.note}</p>
                      </div>
                    ))}
                  </div>
                  <div className="mt-6 rounded-xl bg-green-100 p-4 text-center">
                    <p className="text-xs font-semibold uppercase tracking-wider text-green-600 mb-1">
                      Total LTV
                    </p>
                    <p className="text-2xl font-bold text-green-800">
                      {unitEconomicsBreakdown.totalLTV}
                    </p>
                  </div>
                </CardContent>
              </Card>
            </FadeInOnScroll>

            {/* Center - Gross Margin */}
            <FadeInOnScroll>
              <div className="flex flex-col items-center justify-center text-center py-8 lg:py-16">
                <div className="mb-6">
                  <ArrowDown className="h-8 w-8 text-green-500 mx-auto animate-bounce" />
                </div>
                <div className="rounded-2xl bg-white shadow-lg border-2 border-brand-200 p-8">
                  <p className="text-sm font-semibold uppercase tracking-wider text-brand-600 mb-2">
                    Gross Margin
                  </p>
                  <p className="text-5xl md:text-6xl font-extrabold bg-gradient-to-r from-brand-500 to-brand-700 bg-clip-text text-transparent">
                    {unitEconomicsBreakdown.grossMargin}
                  </p>
                  <p className="mt-3 text-sm text-gray-500 max-w-[200px] mx-auto">
                    Per battery across full lifecycle
                  </p>
                </div>
                <div className="mt-6">
                  <ArrowDown className="h-8 w-8 text-purple-500 mx-auto animate-bounce" />
                </div>
              </div>
            </FadeInOnScroll>

            {/* Cost Column */}
            <FadeInOnScroll direction="right">
              <Card className="border-purple-200 bg-purple-50/50">
                <CardContent>
                  <div className="flex items-center gap-2 mb-6">
                    <Wallet className="h-5 w-5 text-purple-600" />
                    <h3 className="text-lg font-bold text-purple-800">
                      Cost (CAC + COGS)
                    </h3>
                  </div>
                  <div className="space-y-4">
                    {unitEconomicsBreakdown.costs.map((item, idx) => (
                      <div
                        key={idx}
                        className="rounded-lg bg-white p-4 border border-purple-100"
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-semibold text-gray-900">
                            {item.label}
                          </span>
                          <span className="text-sm font-bold text-purple-700">
                            ₹{item.amount.toLocaleString("en-IN")}
                          </span>
                        </div>
                        <p className="text-xs text-gray-500">{item.note}</p>
                      </div>
                    ))}
                  </div>
                  <div className="mt-6 rounded-xl bg-purple-100 p-4 text-center">
                    <p className="text-xs font-semibold uppercase tracking-wider text-purple-600 mb-1">
                      Total CAC + COGS
                    </p>
                    <p className="text-2xl font-bold text-purple-800">
                      {unitEconomicsBreakdown.totalCACCOGS}
                    </p>
                  </div>
                </CardContent>
              </Card>
            </FadeInOnScroll>
          </div>
        </div>
      </section>

      {/* Strategic Sequencing */}
      <section className="py-20 md:py-28 bg-white">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <FadeInOnScroll>
            <SectionHeading
              badge="Go-to-Market"
              title="Strategic Sequencing"
              subtitle="A phased approach that builds the cash flow engine first, then layers recurring revenue and lifecycle moats."
            />
          </FadeInOnScroll>

          <div className="grid gap-6 md:grid-cols-3">
            {[
              {
                phase: "Phase 1",
                title: "Cash Flow Engine",
                description:
                  "Launch with underwriting enablement fees. Immediate revenue from Day 1 through NBFC partnerships and dealer onboarding.",
                color: "brand",
                items: [
                  "Underwriting fee per loan",
                  "Dealer network activation",
                  "NBFC integration",
                ],
              },
              {
                phase: "Phase 2",
                title: "Recurring SaaS + Collection",
                description:
                  "Layer telemetry SaaS subscriptions and collection infrastructure fees for predictable recurring revenue.",
                color: "green",
                items: [
                  "Telemetry SaaS per battery",
                  "Collection platform fees",
                  "Data-driven risk insights",
                ],
              },
              {
                phase: "Phase 3",
                title: "Lifecycle Moat",
                description:
                  "Capture end-of-life value through EPR compliance, battery resale, and recycling partnerships.",
                color: "purple",
                items: [
                  "EPR compliance tooling",
                  "Battery resale / refurbishment",
                  "Recycling margin capture",
                ],
              },
            ].map((phase, idx) => (
              <FadeInOnScroll key={phase.phase} delay={idx * 0.15}>
                <Card className="h-full relative overflow-hidden">
                  <div
                    className={cn(
                      "absolute top-0 left-0 right-0 h-1",
                      idx === 0 && "bg-brand-500",
                      idx === 1 && "bg-accent-green",
                      idx === 2 && "bg-brand-700"
                    )}
                  />
                  <CardContent className="pt-8">
                    <div className="flex items-center gap-3 mb-4">
                      <div
                        className={cn(
                          "flex h-10 w-10 items-center justify-center rounded-full text-white font-bold text-sm",
                          idx === 0 && "bg-brand-500",
                          idx === 1 && "bg-accent-green",
                          idx === 2 && "bg-brand-700"
                        )}
                      >
                        {idx + 1}
                      </div>
                      <div>
                        <p className="text-xs font-semibold uppercase tracking-wider text-gray-500">
                          {phase.phase}
                        </p>
                        <h3 className="text-lg font-bold text-gray-900">
                          {phase.title}
                        </h3>
                      </div>
                    </div>
                    <p className="text-sm text-gray-600 leading-relaxed mb-4">
                      {phase.description}
                    </p>
                    <ul className="space-y-2">
                      {phase.items.map((item) => (
                        <li
                          key={item}
                          className="flex items-center gap-2 text-sm text-gray-700"
                        >
                          <ArrowRight className="h-3.5 w-3.5 text-brand-500 flex-shrink-0" />
                          {item}
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              </FadeInOnScroll>
            ))}
          </div>

          {/* Connecting arrows between phases (desktop) */}
          <div className="hidden md:flex items-center justify-center mt-8 gap-4">
            {["Build Revenue", "Add ARR", "Lock Moat"].map((label, idx) => (
              <div key={label} className="flex items-center gap-4">
                <span className="text-sm font-semibold text-brand-600">
                  {label}
                </span>
                {idx < 2 && (
                  <ArrowRight className="h-5 w-5 text-brand-400" />
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <CTASection
        title="See the Full Investment Thesis"
        subtitle="Understand how iTarang's business model creates compounding value for investors and partners."
        primaryCTA={{ label: "Investor Overview", href: "/for-investors" }}
        secondaryCTA={{ label: "Talk to Founders", href: "/contact" }}
      />
    </>
  );
}
