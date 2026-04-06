"use client";

import { motion } from "framer-motion";
import { useInView } from "react-intersection-observer";
import { cn } from "@/lib/utils";
import { Check } from "lucide-react";
import type { LucideIcon } from "lucide-react";

interface PillarCardProps {
  icon: LucideIcon;
  title: string;
  description: string;
  features: string[];
  keyBenefit: string;
  color: "brand" | "green" | "pink";
}

const colorMap = {
  brand: {
    iconBg: "bg-brand-100",
    iconText: "text-brand-600",
    benefitBg: "bg-brand-50",
    benefitBorder: "border-brand-200",
    benefitText: "text-brand-700",
    check: "text-brand-500",
    accentBar: "bg-brand-500",
  },
  green: {
    iconBg: "bg-green-100",
    iconText: "text-green-600",
    benefitBg: "bg-green-50",
    benefitBorder: "border-green-200",
    benefitText: "text-green-700",
    check: "text-green-500",
    accentBar: "bg-accent-green",
  },
  pink: {
    iconBg: "bg-pink-100",
    iconText: "text-pink-600",
    benefitBg: "bg-pink-50",
    benefitBorder: "border-pink-200",
    benefitText: "text-pink-700",
    check: "text-pink-500",
    accentBar: "bg-accent-sky",
  },
};

export default function PillarCard({
  icon: Icon,
  title,
  description,
  features,
  keyBenefit,
  color,
}: PillarCardProps) {
  const { ref, inView } = useInView({ triggerOnce: true, threshold: 0.15 });
  const c = colorMap[color];

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 30 }}
      animate={inView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.6 }}
      className="relative rounded-2xl border border-gray-100 bg-white shadow-sm overflow-hidden group hover:shadow-lg transition-shadow"
    >
      {/* Top accent bar */}
      <div className={cn("h-1", c.accentBar)} />

      <div className="p-8">
        {/* Icon */}
        <div
          className={cn(
            "flex h-14 w-14 items-center justify-center rounded-2xl",
            c.iconBg
          )}
        >
          <Icon className={cn("h-7 w-7", c.iconText)} />
        </div>

        {/* Title & Description */}
        <h3 className="mt-5 text-xl font-bold text-gray-900">{title}</h3>
        <p className="mt-2 text-sm leading-relaxed text-gray-600">
          {description}
        </p>

        {/* Feature list */}
        <ul className="mt-6 space-y-3">
          {features.map((feature) => (
            <li key={feature} className="flex items-start gap-2.5">
              <Check className={cn("h-4 w-4 mt-0.5 shrink-0", c.check)} />
              <span className="text-sm text-gray-700">{feature}</span>
            </li>
          ))}
        </ul>

        {/* Key benefit callout */}
        <div
          className={cn(
            "mt-6 rounded-xl border p-4",
            c.benefitBg,
            c.benefitBorder
          )}
        >
          <p className={cn("text-sm font-semibold", c.benefitText)}>
            Key Benefit
          </p>
          <p className="mt-1 text-sm text-gray-700">{keyBenefit}</p>
        </div>
      </div>
    </motion.div>
  );
}
