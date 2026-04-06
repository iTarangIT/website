"use client";

import { Briefcase } from "lucide-react";
import { Card, CardContent } from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import { keyHires } from "@/data/team";
import FadeInOnScroll from "@/components/shared/FadeInOnScroll";

export default function HiringPlan() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {keyHires.map((hire, idx) => (
        <FadeInOnScroll key={hire.role} delay={idx * 0.12}>
          <Card className="h-full hover:shadow-md transition-shadow relative overflow-hidden group">
            {/* Top accent */}
            <div className="h-1 bg-gradient-to-r from-accent-sky to-brand-500" />
            <CardContent className="pt-6">
              <div className="flex items-start justify-between mb-4">
                <div className="w-10 h-10 rounded-lg bg-brand-50 flex items-center justify-center shrink-0">
                  <Briefcase className="h-5 w-5 text-brand-600" />
                </div>
                <Badge variant="accent" className="text-[10px]">
                  Open Position
                </Badge>
              </div>

              <h3 className="text-lg font-bold text-gray-900 mb-2">
                {hire.role}
              </h3>
              <p className="text-sm text-gray-600 leading-relaxed">
                {hire.description}
              </p>
            </CardContent>
          </Card>
        </FadeInOnScroll>
      ))}
    </div>
  );
}
