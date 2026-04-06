"use client";

import { Shield, ShieldCheck, Handshake } from "lucide-react";
import FadeInOnScroll from "@/components/shared/FadeInOnScroll";
import { TestimonialCarousel } from "@/components/ui/testimonial";
import { AnimatedGroup } from "@/components/ui/animated-group";

const partners = [
  { icon: Shield, label: "DPIIT Recognised" },
  { icon: ShieldCheck, label: "BIS Certified IoT" },
  { icon: Handshake, label: "Intellicar Partner" },
];

const testimonials = [
  {
    id: 1,
    name: "Rajesh Kumar",
    avatar: "/images/placeholder-avatar.jpg",
    description:
      "Switched from lead-acid to iTarang lithium. My daily earning went up because the battery lasts longer. EMI is easy to manage.",
  },
  {
    id: 2,
    name: "Sunil Sharma",
    avatar: "/images/placeholder-avatar.jpg",
    description:
      "As a dealer, iTarang handles the financing headache. I just sell the battery and they take care of the rest.",
  },
  {
    id: 3,
    name: "Priya Mehta",
    avatar: "/images/placeholder-avatar.jpg",
    description:
      "The IoT dashboard gives us real-time battery health data. This is exactly the visibility lenders need before approving EV battery loans.",
  },
];

export default function SocialProof() {
  return (
    <section className="py-24 md:py-32 bg-white relative overflow-hidden">
      {/* Soft gradient accent */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-[radial-gradient(ellipse,rgba(103,61,230,0.05),transparent_70%)] pointer-events-none" />

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 relative z-10">
        <FadeInOnScroll>
          <div className="text-center mb-12">
            <span className="inline-block text-sm font-semibold text-brand-500 tracking-widest uppercase mb-4">
              Trusted By
            </span>
          </div>

          {/* Partner badges — pill style */}
          <AnimatedGroup
            preset="blur-slide"
            className="flex flex-wrap items-center justify-center gap-4 md:gap-6"
          >
            {partners.map((partner, i) => {
              const Icon = partner.icon;
              return (
                <div
                  key={i}
                  className="flex items-center gap-2.5 px-5 py-2.5 rounded-full bg-surface-warm border border-gray-200/60 text-gray-700 hover:border-brand-300 hover:bg-brand-50/50 transition-all"
                >
                  <Icon className="h-4 w-4 text-brand-500" />
                  <span className="text-sm font-semibold tracking-wide font-sans">
                    {partner.label}
                  </span>
                </div>
              );
            })}
          </AnimatedGroup>

          {/* Divider */}
          <div className="flex items-center justify-center my-14">
            <div className="h-px w-16 bg-gradient-to-r from-transparent via-brand-300/40 to-transparent" />
            <div className="mx-4 w-1.5 h-1.5 rounded-full bg-brand-300/40" />
            <div className="h-px w-16 bg-gradient-to-r from-transparent via-brand-300/40 to-transparent" />
          </div>

          {/* Testimonial carousel */}
          <div className="relative">
            <h3 className="text-center text-lg text-gray-400 mb-8 font-sans">
              What our partners say
            </h3>
            <TestimonialCarousel
              testimonials={testimonials}
              className="max-w-2xl mx-auto"
            />
          </div>
        </FadeInOnScroll>
      </div>
    </section>
  );
}
