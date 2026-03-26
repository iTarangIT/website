"use client";

import { motion } from "framer-motion";
import { staggerContainer, staggerItem } from "@/lib/animations";
import { ArrowRight } from "lucide-react";
import Button from "@/components/ui/Button";
import StatsStrip from "@/components/shared/StatsStrip";
import { heroCounters } from "@/data/metrics";
import Link from "next/link";

export default function HeroSection() {
  return (
    <section className="relative min-h-screen flex flex-col justify-center overflow-hidden bg-gradient-to-b from-brand-900 via-brand-950 to-brand-950">
      {/* Abstract grid/dot pattern overlay */}
      <div
        className="absolute inset-0 opacity-20"
        style={{
          backgroundImage:
            "radial-gradient(circle at 1px 1px, rgba(167,139,250,0.4) 1px, transparent 0)",
          backgroundSize: "40px 40px",
        }}
      />

      {/* Gradient glow accents */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-brand-500/10 rounded-full blur-3xl" />
      <div className="absolute bottom-1/3 right-1/4 w-80 h-80 bg-accent-pink/8 rounded-full blur-3xl" />

      {/* Main content */}
      <div className="relative z-10 mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 pt-32 pb-16">
        <motion.div
          variants={staggerContainer}
          initial="initial"
          animate="animate"
          className="flex flex-col items-center text-center"
        >
          {/* Badge */}
          <motion.div variants={staggerItem}>
            <span className="inline-flex items-center gap-2 rounded-full bg-brand-800/60 border border-brand-600/30 px-4 py-1.5 text-sm font-medium text-brand-200 backdrop-blur-sm">
              <span className="h-1.5 w-1.5 rounded-full bg-accent-green animate-pulse" />
              India&apos;s 1st EV Battery Financing &amp; Lifecycle Management Ecosystem
            </span>
          </motion.div>

          {/* Main heading */}
          <motion.h1
            variants={staggerItem}
            className="mt-8 text-5xl md:text-7xl font-bold text-white leading-tight tracking-tight"
          >
            The Intelligence Layer
            <br />
            <span className="bg-gradient-to-r from-brand-300 via-brand-400 to-accent-pink bg-clip-text text-transparent">
              for India&apos;s EV Battery Economy
            </span>
          </motion.h1>

          {/* Subheading */}
          <motion.p
            variants={staggerItem}
            className="mt-6 text-lg md:text-xl text-brand-200 max-w-3xl leading-relaxed"
          >
            We turn every battery into a programmable financial asset — with real-time
            telemetry, behavioral risk scoring, and full lifecycle management. So NBFCs
            can lend confidently, and drivers can earn more.
          </motion.p>

          {/* CTA buttons */}
          <motion.div
            variants={staggerItem}
            className="mt-10 flex flex-col sm:flex-row items-center gap-4"
          >
            <Button href="/for-investors" size="lg" variant="primary">
              For Investors
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
            <Button
              href="/for-nbfcs"
              size="lg"
              variant="outline"
              className="border-white text-white hover:bg-white/10"
            >
              For Lending Partners
            </Button>
            <Link
              href="/products"
              className="inline-flex items-center justify-center px-8 py-4 text-lg font-semibold text-white/80 hover:text-white transition-colors"
            >
              For Dealers
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </motion.div>
        </motion.div>
      </div>

      {/* Stats strip at the bottom */}
      <div className="relative z-10 mt-auto">
        <StatsStrip stats={heroCounters} />
      </div>
    </section>
  );
}
