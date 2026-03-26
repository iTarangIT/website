"use client";

import { motion } from "framer-motion";
import { useInView } from "react-intersection-observer";
import SectionHeading from "@/components/shared/SectionHeading";
import {
  Lock,
  MapPin,
  Brain,
  Activity,
  Bell,
  AlertTriangle,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

interface RiskFeature {
  icon: LucideIcon;
  title: string;
  description: string;
}

const features: RiskFeature[] = [
  {
    icon: Lock,
    title: "Remote Immobilisation",
    description:
      "Disable charging remotely on default — a credible, non-intrusive recovery lever that reduces collection costs by up to 60%.",
  },
  {
    icon: MapPin,
    title: "GPS Asset Tracking",
    description:
      "Real-time location of every financed battery. Know where your collateral is at all times, enabling faster recovery.",
  },
  {
    icon: Brain,
    title: "Behavioral Risk Scoring",
    description:
      "Proprietary scoring model using charge patterns, usage frequency, and geolocation to predict default 30 days in advance.",
  },
  {
    icon: Activity,
    title: "Real-time SOH Monitoring",
    description:
      "Continuous State of Health tracking ensures collateral value is always known. Alerts trigger on rapid degradation.",
  },
  {
    icon: Bell,
    title: "Automated Collection Signals",
    description:
      "Smart nudges and payment reminders triggered by battery usage. Drivers pay when they earn — aligned incentives.",
  },
  {
    icon: AlertTriangle,
    title: "Predictive Default Alerts",
    description:
      "ML-driven early warning system flags at-risk accounts 30+ days before missed payments, enabling proactive intervention.",
  },
];

export default function RiskFeatures() {
  const { ref, inView } = useInView({ triggerOnce: true, threshold: 0.1 });

  return (
    <section className="py-16 md:py-24 bg-gray-50">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        <SectionHeading
          badge="Risk Mitigation"
          title="Built-In Risk Infrastructure"
          subtitle="Every tool an NBFC needs to underwrite, monitor, and recover EV battery assets confidently."
        />

        <div ref={ref} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 mt-12">
          {features.map((feature, i) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 24 }}
              animate={inView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.5, delay: i * 0.08 }}
              className="group rounded-2xl border border-gray-100 bg-white p-6 shadow-sm hover:shadow-md hover:border-brand-200 transition-all duration-300"
            >
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-brand-50 group-hover:bg-brand-100 transition-colors">
                <feature.icon className="h-6 w-6 text-brand-600" />
              </div>
              <h3 className="mt-4 text-lg font-semibold text-gray-900">
                {feature.title}
              </h3>
              <p className="mt-2 text-sm leading-relaxed text-gray-600">
                {feature.description}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
