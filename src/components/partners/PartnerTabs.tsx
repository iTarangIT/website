"use client";

import { useEffect, useRef, useState } from "react";
import Image from "next/image";
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
  Users,
  Wallet,
  BatteryCharging,
  Headset,
  Layers,
  Repeat,
  Recycle,
  BadgeIndianRupee,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";
import Button from "@/components/ui/Button";

type Tab = {
  id: string;
  label: string;
  icon: LucideIcon;
  color: string;
  activeColor: string;
  iconActiveColor: string;
  borderColor: string;
  headline: string;
  description: string;
  /** Hover border for this tab's feature cards. */
  cardHoverColor: string;
  features: {
    icon: LucideIcon;
    title: string;
    text: string;
    iconBg: string;
    iconColor: string;
  }[];
  cta: string;
  ctaHref: string;
  placeholder: string;
  image: string;
  partnersLabel?: string;
  partners?: { name: string; src: string; width: number; height: number }[];
};

const tabs: Tab[] = [
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
    cardHoverColor: "hover:border-blue-200/70",
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
    image: "/new_images/monitor.png",
    partnersLabel: "Financing & ecosystem partners",
    partners: [
      {
        name: "Bajaj Finserv",
        src: "/logos/bajaj-finserv.png",
        width: 736,
        height: 200,
      },
      {
        name: "BatteryPool",
        src: "/logos/battery_pool_logo.svg",
        width: 189,
        height: 31,
      },
    ],
  },
  {
    id: "dealer",
    label: "For Dealers",
    icon: Store,
    color: "from-emerald-50 to-green-50/50",
    activeColor: "bg-emerald-600",
    iconActiveColor: "text-white",
    borderColor: "border-emerald-200/40",
    headline: "Become the complete lithium shop. We power everything behind it.",
    description:
      "Sell every kind of lithium battery, offer instant EMIs, buy back old batteries, and turn scrap into cash — all through one partner. You grow your business. We handle financing, logistics, and the tech.",
    cardHoverColor: "hover:border-emerald-200/70",
    features: [
      {
        icon: Layers,
        title: "Sell Every Battery, Not Just E-Rickshaw",
        text: "Stock and sell the full lithium range — L2, L3, L4, L5, plus two-wheeler, inverter, and solar batteries. One partner for your entire shop, in every voltage and Ah configuration your customers need.",
        iconBg: "bg-emerald-100",
        iconColor: "text-emerald-600",
      },
      {
        icon: Shield,
        title: "Zero Credit Risk, Financing for Every Driver",
        text: "The loan sits between the driver and the NBFC — never you. And we approve a wide range of driver profiles, so fewer customers walk out empty-handed. You make the sale; we handle approvals and collections.",
        iconBg: "bg-green-100",
        iconColor: "text-green-600",
      },
      {
        icon: Repeat,
        title: "Buyback Keeps Customers Coming Back",
        text: "If a driver no longer wants a battery, we buy it back — priced fairly on its age and condition — and help them switch. Your customer stays happy, stays with you, and comes back for the next purchase.",
        iconBg: "bg-teal-100",
        iconColor: "text-teal-600",
      },
      {
        icon: Recycle,
        title: "Turn Scrap Into Cash",
        text: "We buy old and scrap batteries from you and your drivers at the best rates around. What used to sit dead in your shop now becomes income.",
        iconBg: "bg-emerald-100",
        iconColor: "text-emerald-600",
      },
      {
        icon: Truck,
        title: "We Do the Heavy Lifting",
        text: "We supply stock, process loans, fit the IoT device, and manage collections. You focus on selling.",
        iconBg: "bg-green-100",
        iconColor: "text-green-600",
      },
      {
        icon: BadgeIndianRupee,
        title: "Best Price, Guaranteed",
        text: "Found a lower price elsewhere? Show us the proof and we'll match it. You never lose a sale on price.",
        iconBg: "bg-teal-100",
        iconColor: "text-teal-600",
      },
    ],
    cta: "Become a Dealer Partner",
    ctaHref: "/contact?role=dealer",
    placeholder: "PHOTO: Dealer at their shop with iTarang batteries",
    image: "/new_images/for_dealers.png",
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
    cardHoverColor: "hover:border-amber-200/70",
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
    image: "/new_images/for_oems.png",
  },
  {
    id: "customer",
    label: "For Customers",
    icon: Users,
    color: "from-violet-50 to-purple-50/50",
    activeColor: "bg-violet-600",
    iconActiveColor: "text-white",
    borderColor: "border-violet-200/40",
    headline: "Own a better battery. Pay as you ride.",
    description:
      "Get a lithium battery with easy daily or weekly EMIs. More range, longer life, and support that keeps you earning — no lump sum, no surprises.",
    cardHoverColor: "hover:border-violet-200/70",
    features: [
      {
        icon: Wallet,
        title: "Affordable EMIs",
        text: "Flexible daily or weekly payments that fit your earnings. Get on the road without a big upfront cost.",
        iconBg: "bg-violet-100",
        iconColor: "text-violet-600",
      },
      {
        icon: BatteryCharging,
        title: "Longer Range & Life",
        text: "Lithium batteries go further per charge and last more cycles than lead-acid, so you earn more every day.",
        iconBg: "bg-purple-100",
        iconColor: "text-purple-600",
      },
      {
        icon: Headset,
        title: "Always Supported",
        text: "IoT-monitored batteries mean quick help when you need it. We spot issues before they slow you down.",
        iconBg: "bg-fuchsia-100",
        iconColor: "text-fuchsia-600",
      },
    ],
    cta: "Find a Dealer Near You",
    ctaHref: "/contact?role=customer",
    placeholder: "PHOTO: E-rickshaw driver with iTarang battery",
    image: "/new_images/for_customers.png",
  },
];

export default function PartnerTabs() {
  const [activeTab, setActiveTab] = useState("nbfc");
  const active = tabs.find((t) => t.id === activeTab)!;
  const sectionRef = useRef<HTMLElement>(null);

  const partners = active.partners;

  // Select + scroll to a tab when the URL hash matches one (supports
  // cross-page deep links like /for-partners#nbfc from the home dropdown).
  useEffect(() => {
    const applyHash = () => {
      const id = window.location.hash.slice(1);
      if (!id || !tabs.some((t) => t.id === id)) return;
      setActiveTab(id);
      sectionRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    };
    applyHash();
    window.addEventListener("hashchange", applyHash);
    return () => window.removeEventListener("hashchange", applyHash);
  }, []);

  return (
    <section ref={sectionRef} className="py-20 md:py-28 bg-white [content-visibility:auto] [contain-intrinsic-size:0_2200px]">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        {/* Tab buttons */}
        <div className="flex flex-wrap items-center justify-center gap-2 mb-16">
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
          <div className="flex flex-col md:flex-row gap-12 items-start md:items-center">
            {/* Left — text content */}
            <div className="w-full md:w-1/2">
              <h2 className="text-3xl md:text-4xl text-gray-900 tracking-tight">
                {active.headline}
              </h2>
              <p className="mt-4 text-lg text-gray-500 leading-relaxed font-sans">
                {active.description}
              </p>

              <div className="mt-8">
                <Button href={active.ctaHref} size="lg">
                  {active.cta}
                </Button>
              </div>
            </div>

            {/* Right — photo/screenshot placeholder */}
            <div className="w-full md:w-1/2">
              <div className={`relative rounded-3xl bg-gradient-to-br ${active.color} aspect-[4/3] flex items-center justify-center border ${active.borderColor} overflow-hidden group hover:shadow-lg transition-shadow`}>
                {active.image ? (
                  <Image
                    src={active.image}
                    alt={active.label}
                    fill
                    sizes="(max-width: 768px) calc(100vw - 2rem), 600px"
                    loading="lazy"
                    className="object-cover"
                  />
                ) : (
                  <span className="text-xs text-gray-400 px-4 text-center font-sans group-hover:text-gray-500 transition-colors">
                    {active.placeholder}
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Feature grid — same structure across every tab */}
          <div className="mt-14 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {active.features.map((feature, i) => {
              const FIcon = feature.icon;
              return (
                <motion.div
                  key={feature.title}
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.4, delay: 0.1 + i * 0.06 }}
                  className={cn(
                    "group rounded-2xl p-6",
                    "bg-gradient-to-br from-white to-surface-warm",
                    "border border-gray-200/60 shadow-sm",
                    "transition-all duration-300 hover:-translate-y-1 hover:shadow-lg",
                    active.cardHoverColor
                  )}
                >
                  <div className={`h-10 w-10 rounded-xl ${feature.iconBg} flex items-center justify-center`}>
                    <FIcon className={`h-5 w-5 ${feature.iconColor}`} />
                  </div>
                  <h3 className="mt-4 text-base font-semibold text-gray-900 font-sans">
                    {feature.title}
                  </h3>
                  <p className="mt-2 text-sm text-gray-500 leading-relaxed font-sans">
                    {feature.text}
                  </p>
                </motion.div>
              );
            })}
          </div>

          {/* Partner logo strip — each logo is rendered once to avoid duplicate requests. */}
          {partners && (
            <div className="mt-16 md:mt-20 pt-12 border-t border-gray-200/70">
              <div className="flex flex-col items-center">
                <span className="text-xs font-semibold tracking-[0.18em] uppercase text-gray-400 font-sans">
                  {active.partnersLabel}
                </span>

                <motion.div
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.4, delay: 0.15 }}
                  className="mt-8 flex w-full flex-wrap items-center justify-center gap-4 py-3"
                >
                  {partners.map((partner) => (
                    <div
                      key={partner.name}
                      className="group/logo flex h-24 w-[210px] shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-white to-surface-warm px-7 border border-gray-200/60 shadow-sm transition-all duration-300 hover:-translate-y-1 hover:border-blue-200/70 hover:shadow-lg"
                    >
                      <Image
                        src={partner.src}
                        alt={partner.name}
                        width={partner.width}
                        height={partner.height}
                        loading="lazy"
                        className="h-auto max-h-10 w-auto object-contain opacity-70 grayscale transition-all duration-300 group-hover/logo:opacity-100 group-hover/logo:grayscale-0"
                      />
                    </div>
                  ))}
                </motion.div>
              </div>
            </div>
          )}
        </motion.div>
      </div>
    </section>
  );
}
