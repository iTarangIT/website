"use client";

import { motion } from "framer-motion";
import { fadeUp } from "@/lib/animations";
import Button from "@/components/ui/Button";
import { Calendar, Download, Clock } from "lucide-react";

export default function NBFCContactCTA() {
  return (
    <section className="relative overflow-hidden bg-gradient-to-br from-brand-600 to-brand-900 py-20 md:py-28">
      {/* Background pattern */}
      <div
        className="absolute inset-0 opacity-10"
        style={{
          backgroundImage:
            "radial-gradient(circle at 1px 1px, rgba(255,255,255,0.3) 1px, transparent 0)",
          backgroundSize: "32px 32px",
        }}
      />

      <div className="relative mx-auto max-w-3xl px-4 sm:px-6 lg:px-8 text-center">
        <motion.h2
          {...fadeUp}
          className="text-3xl md:text-4xl lg:text-5xl font-bold text-white"
        >
          Let&apos;s Make Batteries Bankable&mdash;Together
        </motion.h2>

        <motion.p
          {...fadeUp}
          transition={{ ...fadeUp.transition, delay: 0.1 }}
          className="mt-4 text-lg text-white/80 max-w-xl mx-auto"
        >
          Our integration team will walk you through the API, data schema, and
          pilot onboarding process. No commitment required.
        </motion.p>

        <motion.div
          {...fadeUp}
          transition={{ ...fadeUp.transition, delay: 0.25 }}
          className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4"
        >
          <Button
            href="/contact?source=nbfc"
            size="lg"
            className="bg-white text-brand-700 hover:bg-gray-100 shadow-lg gap-2"
          >
            <Calendar className="h-5 w-5" />
            Schedule Integration Discussion
          </Button>
          <Button
            href="/resources/nbfc-partnership-overview.pdf"
            size="lg"
            variant="outline"
            className="border-white text-white hover:bg-white/10 gap-2"
          >
            <Download className="h-5 w-5" />
            Download NBFC Partnership Overview
          </Button>
        </motion.div>

        <motion.p
          {...fadeUp}
          transition={{ ...fadeUp.transition, delay: 0.4 }}
          className="mt-6 flex items-center justify-center gap-2 text-sm text-brand-200"
        >
          <Clock className="h-4 w-4" />
          Typically respond within 2 hours
        </motion.p>
      </div>
    </section>
  );
}
