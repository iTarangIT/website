"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  BarChart3,
  Store,
  Factory,
  Shield,
  Clock,
  Eye,
  TrendingUp,
  Truck,
  FileCheck,
} from "lucide-react";
import { cn } from "@/lib/utils";
import Button from "@/components/ui/Button";
import FadeInOnScroll from "@/components/shared/FadeInOnScroll";

const tabs = [
  {
    id: "nbfc",
    label: "For NBFCs",
    icon: BarChart3,
    color: "from-blue-50 to-indigo-50/50",
    activeColor: "bg-brand-500",
    iconActiveColor: "text-white",
    borderColor: "border-blue-200/40",
    headline: "See inside every battery you finance.",
    description:
      "SOH, location, charge patterns, driver behaviour — all in real-time. If a payment is late, the battery tells us before the collection team finds out.",
    features: [
      {
        icon: Eye,
        title: "Full Asset Visibility",
        text: "Real-time SOH, SOC, GPS, temperature, and charge cycle data for every financed battery.",
        iconBg: "bg-blue-100",
        iconColor: "text-blue-600",
      },
      {
        icon: Shield,
        title: "Risk Intelligence",
        text: "Early warning signals from usage and payment patterns. Know which loans need attention before they go bad.",
        iconBg: "bg-blue-100",
        iconColor: "text-blue-600",
      },
      {
        icon: Clock,
        title: "Live in 4 Weeks",
        text: "API-first integration. Your LOS/LMS connects to our telemetry layer. We handle the field ops.",
        iconBg: "bg-cyan-100",
        iconColor: "text-cyan-600",
      },
    ],
    cta: "Download Partnership Overview",
    ctaHref: "/contact?role=nbfc",
    placeholder: "SCREENSHOT: NBFC Dashboard — portfolio health view",
  },
  {
    id: "dealer",
    label: "For Dealers",
    icon: Store,
    color: "from-emerald-50 to-green-50/50",
    activeColor: "bg-emerald-600",
    iconActiveColor: "text-white",
    borderColor: "border-emerald-200/40",
    headline: "Sell more batteries. We handle the financing.",
    description:
      "Offer lithium batteries with ready EMI financing. Your customers get better batteries. You get better margins and zero credit risk.",
    features: [
      {
        icon: TrendingUp,
        title: "Higher Margins",
        text: "Lithium batteries sell at higher price points with financing built in. More revenue per customer.",
        iconBg: "bg-emerald-100",
        iconColor: "text-emerald-600",
      },
      {
        icon: Truck,
        title: "Full Support",
        text: "We supply batteries, handle loan processing, install IoT devices, and manage collections. You focus on customers.",
        iconBg: "bg-green-100",
        iconColor: "text-green-600",
      },
      {
        icon: Shield,
        title: "Zero Credit Risk",
        text: "Financing is between the driver and the NBFC. You sell, we handle the rest.",
        iconBg: "bg-teal-100",
        iconColor: "text-teal-600",
      },
    ],
    cta: "Become a Dealer Partner",
    ctaHref: "/contact?role=dealer",
    placeholder: "PHOTO: Dealer at their shop with iTarang batteries",
  },
  {
    id: "oem",
    label: "For OEMs",
    icon: Factory,
    color: "from-amber-50 to-orange-50/50",
    activeColor: "bg-amber-600",
    iconActiveColor: "text-white",
    borderColor: "border-amber-200/40",
    headline: "Meet your EPR targets. We track every battery.",
    description:
      "From factory to recycler, every battery has a digital trail. Meet Extended Producer Responsibility compliance with real data, not paperwork.",
    features: [
      {
        icon: FileCheck,
        title: "EPR Compliance",
        text: "Full lifecycle tracking satisfies Extended Producer Responsibility requirements with auditable data.",
        iconBg: "bg-amber-100",
        iconColor: "text-amber-600",
      },
      {
        icon: Eye,
        title: "Battery Passporting",
        text: "Every battery gets a digital identity. Manufacturing data, usage history, health trajectory — all in one record.",
        iconBg: "bg-orange-100",
        iconColor: "text-orange-600",
      },
      {
        icon: TrendingUp,
        title: "Second-Life Routing",
        text: "Batteries reaching end-of-first-life are routed to appropriate second-life applications based on actual health data.",
        iconBg: "bg-yellow-100",
        iconColor: "text-yellow-600",
      },
    ],
    cta: "Explore OEM Integration",
    ctaHref: "/contact?role=oem",
    placeholder: "PHOTO: Battery manufacturing / quality check",
  },
];

export default function PartnerTabs() {
  const [activeTab, setActiveTab] = useState("nbfc");
  const active = tabs.find((t) => t.id === activeTab)!;

  return (
    <section className="py-20 md:py-28 bg-white">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        {/* Tab buttons */}
        <div className="flex items-center justify-center gap-2 mb-16">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  "flex items-center gap-2 px-5 py-2.5 rounded-full text-sm font-medium transition-all font-sans",
                  isActive
                    ? `${tab.activeColor} text-white shadow-lg`
                    : "bg-surface-warm text-gray-600 hover:bg-surface-cream border border-gray-200/40"
                )}
              >
                <Icon className={cn("h-4 w-4", isActive ? tab.iconActiveColor : "text-gray-400")} />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Tab content */}
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <div className="flex flex-col md:flex-row gap-12 items-start">
            {/* Left — text content */}
            <div className="w-full md:w-1/2">
              <h2 className="text-3xl md:text-4xl text-gray-900 tracking-tight">
                {active.headline}
              </h2>
              <p className="mt-4 text-lg text-gray-500 leading-relaxed font-sans">
                {active.description}
              </p>

              <div className="mt-8 space-y-5">
                {active.features.map((feature) => {
                  const FIcon = feature.icon;
                  return (
                    <div key={feature.title} className="flex gap-4">
                      <div className={`flex-shrink-0 h-10 w-10 rounded-xl ${feature.iconBg} flex items-center justify-center`}>
                        <FIcon className={`h-5 w-5 ${feature.iconColor}`} />
                      </div>
                      <div>
                        <h3 className="text-base font-semibold text-gray-900 font-sans">
                          {feature.title}
                        </h3>
                        <p className="mt-1 text-sm text-gray-500 leading-relaxed font-sans">
                          {feature.text}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>

              <div className="mt-8">
                <Button href={active.ctaHref} size="lg">
                  {active.cta}
                </Button>
              </div>
            </div>

            {/* Right — photo/screenshot placeholder */}
            <div className="w-full md:w-1/2">
              <div className={`rounded-3xl bg-gradient-to-br ${active.color} aspect-[4/3] flex items-center justify-center border ${active.borderColor} overflow-hidden group hover:shadow-lg transition-shadow`}>
                <span className="text-xs text-gray-400 px-4 text-center font-sans group-hover:text-gray-500 transition-colors">
                  {active.placeholder}
                </span>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
