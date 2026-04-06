"use client";

import { motion } from "framer-motion";
import { staggerContainer, staggerItem } from "@/lib/animations";
import { ArrowDown } from "lucide-react";
import Button from "@/components/ui/Button";
import Link from "next/link";
import { GridPattern } from "@/components/ui/grid-pattern";
import { cn } from "@/lib/utils";

export default function HeroSection() {
  return (
    <section className="relative min-h-screen flex flex-col justify-center overflow-hidden">
      {/* Background — rich layered dark with warm undertone */}
      <div className="absolute inset-0 bg-brand-950">
        {/* Warm gradient layer */}
        <div className="absolute inset-0 bg-gradient-to-br from-brand-950 via-brand-900/90 to-brand-950" />

        {/* Ambient glow — top left blue */}
        <div className="absolute -top-40 -left-40 w-[600px] h-[600px] rounded-full bg-brand-500/10 blur-[120px]" />

        {/* Ambient glow — bottom right amber */}
        <div className="absolute -bottom-20 -right-20 w-[400px] h-[400px] rounded-full bg-accent-amber/8 blur-[100px]" />

        {/* Grid pattern with organic mask */}
        <GridPattern
          width={48}
          height={48}
          squares={[
            [4, 4], [5, 1], [8, 2], [5, 3], [5, 5],
            [10, 10], [12, 15], [15, 10], [10, 15],
          ]}
          className={cn(
            "fill-brand-400/5 stroke-brand-400/8",
            "[mask-image:radial-gradient(700px_circle_at_30%_50%,white,transparent)]",
          )}
        />

        {/* Grain texture */}
        <div className="absolute inset-0 opacity-[0.02] bg-[url('data:image/svg+xml,%3Csvg%20viewBox%3D%220%200%20256%20256%22%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%3E%3Cfilter%20id%3D%22n%22%3E%3CfeTurbulence%20type%3D%22fractalNoise%22%20baseFrequency%3D%220.9%22%20numOctaves%3D%224%22%20stitchTiles%3D%22stitch%22%2F%3E%3C%2Ffilter%3E%3Crect%20width%3D%22100%25%22%20height%3D%22100%25%22%20filter%3D%22url(%23n)%22%2F%3E%3C%2Fsvg%3E')] bg-repeat bg-[length:128px]" />
      </div>

      {/* Main content */}
      <div className="relative z-10 mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 pt-32 pb-20">
        <motion.div
          variants={staggerContainer}
          initial="initial"
          animate="animate"
          className="max-w-4xl"
        >
          {/* Eyebrow label */}
          <motion.div variants={staggerItem} className="mb-6">
            <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-brand-500/10 border border-brand-400/20 text-brand-300 text-sm font-medium tracking-wide">
              <span className="w-1.5 h-1.5 rounded-full bg-accent-green animate-pulse" />
              Full Lifecycle Battery Platform
            </span>
          </motion.div>

          {/* Main heading — DM Serif Display via global h1 rule */}
          <motion.h1
            variants={staggerItem}
            className="text-5xl md:text-7xl lg:text-[5.5rem] text-white leading-[1.05] tracking-tight"
          >
            Every Battery.
            <br />
            <span className="bg-gradient-to-r from-brand-300 via-accent-amber to-accent-sky bg-clip-text text-transparent">
              From First Charge to Last.
            </span>
          </motion.h1>

          {/* Subheading */}
          <motion.p
            variants={staggerItem}
            className="mt-8 text-xl md:text-2xl text-white/60 max-w-2xl leading-relaxed font-light"
          >
            We finance, monitor, maintain, recover, and recycle EV batteries
            across India. One platform. Every stage.
          </motion.p>

          {/* CTA row */}
          <motion.div
            variants={staggerItem}
            className="mt-10 flex flex-wrap items-center gap-4"
          >
            <Button href="#lifecycle" size="lg" variant="primary" className="shadow-xl shadow-brand-500/30">
              See How It Works
              <ArrowDown className="ml-2 h-4 w-4" />
            </Button>
            <Link
              href="/for-investors"
              className="group flex items-center gap-1.5 text-sm font-medium text-white/40 hover:text-white/70 transition-colors px-4 py-3"
            >
              For Investors
              <span className="group-hover:translate-x-0.5 transition-transform">&rarr;</span>
            </Link>
          </motion.div>
        </motion.div>
      </div>

      {/* Bottom fade into next section */}
      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-surface-warm to-transparent" />
    </section>
  );
}
