"use client";

import { complianceAreas } from "@/data/regulatory";
import { cn } from "@/lib/utils";
import Badge from "@/components/ui/Badge";
import { Card, CardContent } from "@/components/ui/Card";
import FadeInOnScroll from "@/components/shared/FadeInOnScroll";
import { CheckCircle, Shield, TrendingUp } from "lucide-react";

const typeConfig: Record<
  string,
  { variant: "success" | "warning" | "default"; icon: typeof Shield }
> = {
  "Strong Tailwind": { variant: "success", icon: TrendingUp },
  Compliance: { variant: "warning", icon: Shield },
  "Strategic Pivot": { variant: "default", icon: CheckCircle },
};

export default function ComplianceCards() {
  return (
    <div className="grid gap-8 md:grid-cols-3">
      {complianceAreas.map((area, idx) => {
        const config = typeConfig[area.type] || typeConfig["Compliance"];
        const Icon = config.icon;

        return (
          <FadeInOnScroll key={area.title} delay={idx * 0.1}>
            <Card className="h-full flex flex-col">
              <CardContent className="flex flex-col flex-1">
                <div className="flex items-start justify-between gap-3 mb-4">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-100">
                    <Icon className="h-5 w-5 text-brand-600" />
                  </div>
                  <Badge variant={config.variant}>{area.type}</Badge>
                </div>

                <h3 className="text-lg font-bold text-gray-900 mb-4">
                  {area.title}
                </h3>

                <ul className="space-y-3 mb-6 flex-1">
                  {area.points.map((point, pIdx) => (
                    <li
                      key={pIdx}
                      className="flex items-start gap-2 text-sm text-gray-600 leading-relaxed"
                    >
                      <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-brand-400" />
                      {point}
                    </li>
                  ))}
                </ul>

                <div
                  className={cn(
                    "rounded-xl p-4",
                    area.type === "Strong Tailwind"
                      ? "bg-green-50 border border-green-200"
                      : area.type === "Compliance"
                        ? "bg-yellow-50 border border-yellow-200"
                        : "bg-brand-50 border border-brand-200"
                  )}
                >
                  <p className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-1">
                    Our Advantage
                  </p>
                  <p className="text-sm font-medium text-gray-800">
                    {area.advantage}
                  </p>
                </div>
              </CardContent>
            </Card>
          </FadeInOnScroll>
        );
      })}
    </div>
  );
}
