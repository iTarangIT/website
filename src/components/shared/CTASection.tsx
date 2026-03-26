"use client";

import { cn } from "@/lib/utils";
import { motion } from "framer-motion";
import { fadeUp } from "@/lib/animations";
import Button from "@/components/ui/Button";

interface CTASectionProps {
  title: string;
  subtitle: string;
  primaryCTA: { label: string; href: string };
  secondaryCTA?: { label: string; href: string };
  className?: string;
}

export default function CTASection({
  title,
  subtitle,
  primaryCTA,
  secondaryCTA,
  className,
}: CTASectionProps) {
  return (
    <section
      className={cn(
        "relative overflow-hidden bg-gradient-to-br from-brand-500 to-brand-700 py-20 md:py-28",
        className
      )}
    >
      {/* Subtle background pattern */}
      <div
        className="absolute inset-0 opacity-10"
        style={{
          backgroundImage:
            "radial-gradient(circle at 1px 1px, rgba(255,255,255,0.3) 1px, transparent 0)",
          backgroundSize: "32px 32px",
        }}
      />

      <div className="relative mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 text-center">
        <motion.h2
          {...fadeUp}
          className="text-3xl md:text-4xl lg:text-5xl font-bold text-white"
        >
          {title}
        </motion.h2>

        <motion.p
          {...fadeUp}
          transition={{ ...fadeUp.transition, delay: 0.15 }}
          className="mt-4 text-lg md:text-xl text-white/80 max-w-2xl mx-auto"
        >
          {subtitle}
        </motion.p>

        <motion.div
          {...fadeUp}
          transition={{ ...fadeUp.transition, delay: 0.3 }}
          className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4"
        >
          <Button href={primaryCTA.href} size="lg" className="bg-white text-brand-700 hover:bg-gray-100 shadow-lg">
            {primaryCTA.label}
          </Button>
          {secondaryCTA && (
            <Button
              href={secondaryCTA.href}
              size="lg"
              variant="outline"
              className="border-white text-white hover:bg-white/10"
            >
              {secondaryCTA.label}
            </Button>
          )}
        </motion.div>
      </div>
    </section>
  );
}
