"use client";

import { batteryProducts } from "@/data/products";
import Button from "@/components/ui/Button";
import FadeInOnScroll from "@/components/shared/FadeInOnScroll";
import { Zap, Shield } from "lucide-react";

export default function BatterySpecs() {
  return (
    <section className="py-20 md:py-28 bg-white">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <FadeInOnScroll>
          <div className="text-center mb-14">
            <span className="inline-block text-sm font-semibold text-brand-500 tracking-widest uppercase mb-4 font-sans">
              Product Range
            </span>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl text-gray-900 tracking-tight">
              Our Batteries
            </h2>
            <p className="mt-4 text-lg text-gray-500 max-w-2xl mx-auto font-sans">
              Lithium-ion batteries built for Indian e-rickshaws and e-autos.
              Every unit ships with IoT telemetry built in.
            </p>
          </div>
        </FadeInOnScroll>

        <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
          {batteryProducts.slice(0, 3).map((battery, i) => (
            <FadeInOnScroll key={battery.id} delay={i * 0.1}>
              <div className="group h-full flex flex-col rounded-3xl border border-gray-200/60 bg-white shadow-lg shadow-gray-900/5 hover:shadow-xl hover:shadow-brand-500/5 hover:border-brand-200/50 transition-all overflow-hidden">
                {/* Photo placeholder with gradient */}
                <div className="bg-gradient-to-br from-brand-50 to-surface-cream h-44 flex items-center justify-center relative overflow-hidden">
                  <div className="absolute top-3 right-3 flex gap-1.5">
                    {battery.badge && (
                      <span className="px-2.5 py-1 text-[10px] font-semibold rounded-full bg-brand-500 text-white font-sans uppercase tracking-wider">
                        {battery.badge}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2 text-gray-400">
                    <Zap className="h-5 w-5" />
                    <span className="text-sm font-sans">
                      {battery.name}
                    </span>
                  </div>
                </div>

                <div className="flex-1 flex flex-col p-6">
                  <h3 className="text-lg font-bold text-gray-900 font-sans">
                    {battery.name}
                  </h3>

                  {/* Specs */}
                  <div className="mt-5 space-y-3 text-sm flex-1">
                    {[
                      { label: "Capacity", value: `${battery.capacity}Ah / ${battery.energy}` },
                      { label: "Weight", value: battery.weight },
                      { label: "Cycle Life", value: `${battery.cycleLife.toLocaleString()}+` },
                      { label: "Warranty", value: battery.warranty },
                      { label: "Dimensions", value: battery.dimensions },
                    ].map((spec) => (
                      <div key={spec.label} className="flex justify-between items-center">
                        <span className="text-gray-400 font-sans text-xs uppercase tracking-wider">{spec.label}</span>
                        <span className="font-medium text-gray-900 font-sans text-sm">{spec.value}</span>
                      </div>
                    ))}
                  </div>

                  {/* IoT badge */}
                  <div className="mt-5 flex items-center gap-2 rounded-xl bg-brand-50/60 px-3 py-2">
                    <Shield className="h-3.5 w-3.5 text-brand-500" />
                    <span className="text-xs font-medium text-brand-600 font-sans">IoT telemetry included</span>
                  </div>

                  {/* Price + CTA */}
                  <div className="mt-5 pt-5 border-t border-gray-100 flex items-center justify-between">
                    <div>
                      <span className="text-2xl font-bold text-gray-900">
                        ₹{battery.price.toLocaleString("en-IN")}
                      </span>
                      <span className="text-xs text-gray-400 ml-1 font-sans">MRP</span>
                    </div>
                    <Button href="/contact" size="sm">
                      Get a Quote
                    </Button>
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
