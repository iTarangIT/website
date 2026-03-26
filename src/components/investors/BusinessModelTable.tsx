"use client";

import { motion } from "framer-motion";
import {
  FileCheck,
  Activity,
  Wallet,
  Recycle,
} from "lucide-react";
import { revenueStreams, type RevenueStream } from "@/data/revenue-streams";
import Badge from "@/components/ui/Badge";
import SectionHeading from "@/components/shared/SectionHeading";
import FadeInOnScroll from "@/components/shared/FadeInOnScroll";
import { staggerContainer, staggerItem } from "@/lib/animations";

const iconMap: Record<string, React.ElementType> = {
  FileCheck,
  Activity,
  Wallet,
  Recycle,
};

const phaseBadgeVariant = (phase: string): "default" | "success" | "warning" | "accent" => {
  if (phase.includes("Day 1")) return "success";
  if (phase.includes("Phase 2")) return "warning";
  return "default";
};

const natureBadgeVariant = (nature: string): "default" | "success" | "warning" | "accent" => {
  if (nature.includes("ARR")) return "default";
  if (nature.includes("Cash Flow")) return "success";
  if (nature.includes("Volume")) return "warning";
  if (nature.includes("Moat")) return "accent";
  return "default";
};

export default function BusinessModelTable() {
  return (
    <section className="py-20 md:py-28 bg-gray-50">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <FadeInOnScroll>
          <SectionHeading
            badge="Business Model"
            title="Four Revenue Streams, Compounding Value"
            subtitle="A layered monetization model that starts generating cash from Day 1 and deepens with every battery in the network."
          />
        </FadeInOnScroll>

        {/* Desktop table view */}
        <FadeInOnScroll>
          <div className="hidden lg:block overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm">
            {/* Table header */}
            <div className="grid grid-cols-12 gap-4 bg-brand-50 px-6 py-4 text-xs font-semibold uppercase tracking-wider text-brand-700">
              <div className="col-span-3">Revenue Stream</div>
              <div className="col-span-2">Phase / Timing</div>
              <div className="col-span-4">Unit Economics</div>
              <div className="col-span-3">Nature</div>
            </div>

            {/* Table rows */}
            {revenueStreams.map((stream: RevenueStream, i: number) => {
              const Icon = iconMap[stream.icon] || FileCheck;
              return (
                <div
                  key={stream.name}
                  className={`grid grid-cols-12 gap-4 items-center px-6 py-5 ${
                    i < revenueStreams.length - 1 ? "border-b border-gray-100" : ""
                  } hover:bg-gray-50/50 transition-colors`}
                >
                  <div className="col-span-3 flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-50 shrink-0">
                      <Icon className="h-5 w-5 text-brand-500" />
                    </div>
                    <div>
                      <p className="font-semibold text-gray-900 text-sm">
                        {stream.name}
                      </p>
                      <p className="text-xs text-gray-500 mt-0.5">
                        {stream.description}
                      </p>
                    </div>
                  </div>
                  <div className="col-span-2">
                    <Badge variant={phaseBadgeVariant(stream.phase)}>
                      {stream.phase}
                    </Badge>
                  </div>
                  <div className="col-span-4">
                    <p className="text-sm font-medium text-gray-700">
                      {stream.unitEconomics}
                    </p>
                  </div>
                  <div className="col-span-3">
                    <Badge variant={natureBadgeVariant(stream.nature)}>
                      {stream.nature}
                    </Badge>
                  </div>
                </div>
              );
            })}
          </div>
        </FadeInOnScroll>

        {/* Mobile card view */}
        <motion.div
          variants={staggerContainer}
          initial="initial"
          whileInView="animate"
          viewport={{ once: true, amount: 0.1 }}
          className="lg:hidden grid grid-cols-1 sm:grid-cols-2 gap-6"
        >
          {revenueStreams.map((stream: RevenueStream) => {
            const Icon = iconMap[stream.icon] || FileCheck;
            return (
              <motion.div
                key={stream.name}
                variants={staggerItem}
                transition={{ duration: 0.5 }}
                className="rounded-2xl border border-gray-100 bg-white p-6 shadow-sm"
              >
                <div className="flex items-center gap-3 mb-4">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-50 shrink-0">
                    <Icon className="h-5 w-5 text-brand-500" />
                  </div>
                  <h3 className="font-semibold text-gray-900">{stream.name}</h3>
                </div>

                <p className="text-sm text-gray-500 mb-4">{stream.description}</p>

                <div className="space-y-3">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-1">
                      Timing
                    </p>
                    <Badge variant={phaseBadgeVariant(stream.phase)}>
                      {stream.phase}
                    </Badge>
                  </div>
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-1">
                      Unit Economics
                    </p>
                    <p className="text-sm font-medium text-gray-700">
                      {stream.unitEconomics}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-1">
                      Nature
                    </p>
                    <Badge variant={natureBadgeVariant(stream.nature)}>
                      {stream.nature}
                    </Badge>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </motion.div>
      </div>
    </section>
  );
}
