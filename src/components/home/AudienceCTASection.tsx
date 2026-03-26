"use client";

import Link from "next/link";
import { TrendingUp, Building2, Store, ArrowRight } from "lucide-react";
import FadeInOnScroll from "@/components/shared/FadeInOnScroll";

interface AudiencePath {
  icon: React.ElementType;
  title: string;
  description: string;
  href: string;
}

const audiences: AudiencePath[] = [
  {
    icon: TrendingUp,
    title: "For Investors",
    description: "See the data behind the thesis",
    href: "/for-investors",
  },
  {
    icon: Building2,
    title: "For Lending Partners",
    description: "Integrate battery intelligence into your lending",
    href: "/for-nbfcs",
  },
  {
    icon: Store,
    title: "For Dealers",
    description: "Offer financed IoT-enabled batteries",
    href: "/products",
  },
];

export default function AudienceCTASection() {
  return (
    <section className="py-20 md:py-28 bg-white">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {audiences.map((audience, i) => {
            const Icon = audience.icon;
            return (
              <FadeInOnScroll key={audience.title} delay={i * 0.12}>
                <Link
                  href={audience.href}
                  className="group relative flex flex-col justify-between rounded-2xl bg-brand-800 p-8 text-white overflow-hidden hover:scale-[1.02] transition-transform duration-300 min-h-[200px]"
                >
                  {/* Subtle background pattern */}
                  <div
                    className="absolute inset-0 opacity-5"
                    style={{
                      backgroundImage:
                        "radial-gradient(circle at 1px 1px, rgba(255,255,255,0.5) 1px, transparent 0)",
                      backgroundSize: "24px 24px",
                    }}
                  />

                  <div className="relative z-10">
                    <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-white/10 mb-5">
                      <Icon className="h-6 w-6 text-brand-200" />
                    </div>

                    <h3 className="text-xl font-bold mb-2">{audience.title}</h3>
                    <p className="text-brand-200 text-sm">{audience.description}</p>
                  </div>

                  <div className="relative z-10 mt-6 flex items-center gap-2 text-sm font-semibold text-brand-300 group-hover:text-white transition-colors">
                    Learn More
                    <ArrowRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
                  </div>
                </Link>
              </FadeInOnScroll>
            );
          })}
        </div>
      </div>
    </section>
  );
}
