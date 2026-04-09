"use client";

import FadeInOnScroll from "@/components/shared/FadeInOnScroll";

const advantages = [
  { title: "DPIIT Recognised Startup", description: "Government-recognised innovation in EV energy storage and smart battery technology" },
  { title: "BIS Certified IoT Integration", description: "Bureau of Indian Standards certified telemetry for real-time battery health monitoring" },
  { title: "3-Year Warranty on Batteries", description: "Industry-leading warranty backed by 2,000+ cycle LiFePO4 chemistry" },
  { title: "Pan-India Dealer Network", description: "Growing dealer and service network across major Indian cities and EV hubs" },
  { title: "Smart BMS on Every Product", description: "Built-in Battery Management System with overcharge, over-discharge, and thermal protection" },
  { title: "CC-CV Smart Charging", description: "Constant Current–Constant Voltage algorithm across all chargers for maximum battery lifespan" },
  { title: "Designed for Indian Conditions", description: "Engineered for high temperatures, voltage fluctuations, and rough road vibrations" },
  { title: "EMI & Financing Options", description: "Affordable daily EMI plans so drivers can upgrade without large upfront payments" },
];

export default function WhyITarang() {
  return (
    <section className="py-16 md:py-24 bg-white">
      <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-10">
          <span className="inline-block text-sm font-semibold text-brand-500 tracking-widest uppercase mb-4 font-sans">
            The iTarang Advantage
          </span>
          <h2 className="font-sans text-3xl sm:text-4xl font-bold text-gray-900 tracking-tight">
            Why Choose <span className="text-brand-600">iTarang?</span>
          </h2>
          <p className="mt-4 text-lg text-gray-500 max-w-2xl mx-auto font-sans">
            Every product is backed by certified technology, smart monitoring, and a commitment to Indian EV infrastructure.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 md:gap-4">
          {advantages.map((adv, i) => (
            <FadeInOnScroll key={adv.title} delay={i * 0.05}>
              <div className="flex items-start gap-4 px-5 py-4 bg-[#f8fafc] border border-[#e2e8f4] rounded-lg transition-all duration-250 hover:bg-brand-50 hover:border-brand-300 hover:translate-x-1 group">
                <div className="flex-shrink-0 w-2.5 h-2.5 mt-1.5 rounded-full bg-brand-500 shadow-[0_0_6px_rgba(19,143,198,0.4)]" />
                <div className="flex-1 min-w-0">
                  <div className="font-sans text-[15px] font-bold text-[#0a2540] group-hover:text-brand-600 transition-colors">
                    {adv.title}
                  </div>
                  <div className="font-sans text-[13px] text-[#64748b] leading-snug mt-1">
                    {adv.description}
                  </div>
                </div>
              </div>
            </FadeInOnScroll>
          ))}
        </div>
      </div>
    </section>
  );
}
