import { cn } from "@/lib/utils";
import { Shield, ShieldCheck, Handshake } from "lucide-react";

interface TrustBadgeStripProps {
  className?: string;
}

const trustBadges = [
  { icon: Shield, label: "DPIIT Recognised" },
  { icon: ShieldCheck, label: "BIS Certified IoT" },
  { icon: Handshake, label: "Intellicar Partner" },
];

export default function TrustBadgeStrip({ className }: TrustBadgeStripProps) {
  return (
    <section
      className={cn(
        "bg-gray-50 py-6 border-y border-gray-200",
        className
      )}
    >
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex flex-wrap items-center justify-center gap-8 md:gap-16">
          {trustBadges.map((badge, i) => (
            <div
              key={i}
              className="flex items-center gap-2.5 text-gray-700"
            >
              <badge.icon className="h-5 w-5 text-brand-500" />
              <span className="text-sm font-semibold tracking-wide">
                {badge.label}
              </span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
