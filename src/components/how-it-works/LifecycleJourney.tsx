"use client";

import {
  Banknote,
  Truck,
  Activity,
  Wrench,
  RotateCcw,
  Recycle,
} from "lucide-react";
import FadeInOnScroll from "@/components/shared/FadeInOnScroll";

const stageColors = [
  { bg: "from-blue-50 to-indigo-50/50", border: "border-blue-200/40", iconBg: "bg-blue-100", iconColor: "text-blue-600", stepColor: "text-blue-400", statBg: "bg-blue-50", statText: "text-blue-700" },
  { bg: "from-blue-50 to-indigo-50/50", border: "border-blue-200/40", iconBg: "bg-blue-100", iconColor: "text-blue-600", stepColor: "text-blue-400", statBg: "bg-blue-50", statText: "text-blue-700" },
  { bg: "from-cyan-50 to-teal-50/50", border: "border-cyan-200/40", iconBg: "bg-cyan-100", iconColor: "text-cyan-600", stepColor: "text-cyan-400", statBg: "bg-cyan-50", statText: "text-cyan-700" },
  { bg: "from-amber-50 to-orange-50/50", border: "border-amber-200/40", iconBg: "bg-amber-100", iconColor: "text-amber-600", stepColor: "text-amber-400", statBg: "bg-amber-50", statText: "text-amber-700" },
  { bg: "from-emerald-50 to-green-50/50", border: "border-emerald-200/40", iconBg: "bg-emerald-100", iconColor: "text-emerald-600", stepColor: "text-emerald-400", statBg: "bg-emerald-50", statText: "text-emerald-700" },
  { bg: "from-rose-50 to-pink-50/50", border: "border-rose-200/40", iconBg: "bg-rose-100", iconColor: "text-rose-600", stepColor: "text-rose-400", statBg: "bg-rose-50", statText: "text-rose-700" },
];

const stages = [
  {
    icon: Banknote,
    step: "01",
    title: "Finance",
    description:
      "Drivers get a lithium battery on EMI. NBFCs get IoT-backed risk data before they approve.",
    stat: "₹49K avg loan, 18-month tenure",
    detail:
      "90% of e-rickshaw batteries are financed informally at 30-60% interest. We bring formal lending with real data backing every loan.",
    placeholder: "PHOTO: Driver signing finance docs at dealer",
  },
  {
    icon: Truck,
    step: "02",
    title: "Deploy",
    description:
      "Dealer installs the battery + IoT device. Driver is live in 24 hours.",
    stat: "24-hour activation",
    detail:
      "The IoT module is pre-configured. Dealer swaps the battery, pairs the device, and the driver starts earning the same day.",
    placeholder: "PHOTO: Battery installation in e-rickshaw",
  },
  {
    icon: Activity,
    step: "03",
    title: "Monitor",
    description:
      "Real-time SOH, SOC, location, temperature, charge cycles. Every battery has a heartbeat.",
    stat: "150+ batteries tracked live",
    detail:
      "Our dashboard shows every battery's vital signs. Lenders see portfolio health. Dealers see warranty claims forming. Nobody flies blind.",
    placeholder: "SCREENSHOT: IoT Dashboard",
  },
  {
    icon: Wrench,
    step: "04",
    title: "Maintain",
    description:
      "Alerts for anomalies before they become failures. Extend battery life by 20-30%.",
    stat: "20-30% life extension",
    detail:
      "Temperature spikes, deep discharge patterns, abnormal charge cycles — the system catches problems early and routes to the nearest service point.",
    placeholder: "PHOTO: Technician servicing a battery",
  },
  {
    icon: RotateCcw,
    step: "05",
    title: "Buyback",
    description:
      "When the battery reaches end-of-first-life, we buy it back. Fair price based on actual health data.",
    stat: "98% recovery rate",
    detail:
      "No guesswork. The buyback price reflects real SOH data collected over the battery's entire life. Drivers get fair value. Second-life applications get quality cells.",
    placeholder: "PHOTO: Collected batteries at warehouse",
  },
  {
    icon: Recycle,
    step: "06",
    title: "Recycle",
    description:
      "Partnered recyclers extract cobalt, lithium, and nickel. Full EPR compliance for OEMs. Zero waste.",
    stat: "Full EPR compliance",
    detail:
      "Every battery is tracked from factory to recycler. OEMs meet Extended Producer Responsibility targets. Critical minerals re-enter the supply chain.",
    placeholder: "PHOTO: Recycling facility / mineral extraction",
  },
];

export default function LifecycleJourney() {
  return (
    <section id="lifecycle-journey" className="py-20 md:py-28 bg-white">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        <FadeInOnScroll>
          <div className="text-center mb-16">
            <span className="inline-block text-sm font-semibold text-brand-500 tracking-widest uppercase mb-4 font-sans">
              Six Stages
            </span>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl text-gray-900 tracking-tight">
              The Journey of Every Battery
            </h2>
            <p className="mt-4 text-lg text-gray-500 max-w-2xl mx-auto font-sans">
              From the moment a driver gets a battery to the moment its minerals
              are recovered — every step is tracked, managed, and optimised.
            </p>
          </div>
        </FadeInOnScroll>

        {/* Alternating left-right layout with unique colors */}
        <div className="space-y-12 md:space-y-20">
          {stages.map((stage, i) => {
            const Icon = stage.icon;
            const color = stageColors[i];
            const isEven = i % 2 === 0;

            return (
              <FadeInOnScroll
                key={stage.step}
                direction={isEven ? "left" : "right"}
                delay={0.1}
              >
                <div
                  className={`flex flex-col gap-8 ${
                    isEven ? "md:flex-row" : "md:flex-row-reverse"
                  } items-center`}
                >
                  {/* Photo placeholder with colored gradient */}
                  <div className="w-full md:w-1/2">
                    <div className={`rounded-3xl bg-gradient-to-br ${color.bg} aspect-[4/3] flex items-center justify-center border ${color.border} overflow-hidden group hover:shadow-lg transition-shadow`}>
                      <span className="text-xs text-gray-400 px-4 text-center font-sans group-hover:text-gray-500 transition-colors">
                        {stage.placeholder}
                      </span>
                    </div>
                  </div>

                  {/* Content */}
                  <div className="w-full md:w-1/2">
                    <div className="flex items-center gap-3 mb-4">
                      <span className={`text-sm font-bold ${color.stepColor} font-mono`}>
                        {stage.step}
                      </span>
                      <div className={`w-8 h-8 rounded-lg ${color.iconBg} flex items-center justify-center`}>
                        <Icon className={`h-4 w-4 ${color.iconColor}`} />
                      </div>
                    </div>
                    <h3 className="text-2xl md:text-3xl text-gray-900 tracking-tight">
                      {stage.title}
                    </h3>
                    <p className="mt-3 text-lg text-gray-600 leading-relaxed font-sans">
                      {stage.description}
                    </p>
                    <p className="mt-3 text-sm text-gray-500 leading-relaxed font-sans">
                      {stage.detail}
                    </p>
                    <div className={`mt-5 inline-flex items-center rounded-full ${color.statBg} px-4 py-1.5 text-sm font-semibold ${color.statText} font-sans`}>
                      {stage.stat}
                    </div>
                  </div>
                </div>
              </FadeInOnScroll>
            );
          })}
        </div>
      </div>
    </section>
  );
}
