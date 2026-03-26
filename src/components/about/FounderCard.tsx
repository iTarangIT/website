"use client";

import { User, CheckCircle2 } from "lucide-react";
import { Card, CardContent } from "@/components/ui/Card";
import { founders } from "@/data/team";
import FadeInOnScroll from "@/components/shared/FadeInOnScroll";

export default function FounderCard() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
      {founders.map((founder, idx) => (
        <FadeInOnScroll
          key={founder.role}
          delay={idx * 0.15}
          direction={idx === 0 ? "left" : "right"}
        >
          <Card className="h-full hover:shadow-lg transition-shadow">
            <CardContent className="pt-8 pb-8">
              <div className="flex flex-col items-center text-center mb-6">
                {/* Avatar placeholder */}
                <div className="w-20 h-20 rounded-full bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center mb-4 shadow-lg shadow-brand-500/20">
                  <User className="h-9 w-9 text-white" />
                </div>
                <h3 className="text-xl font-bold text-gray-900">
                  {founder.name}
                </h3>
                <p className="text-sm font-semibold text-brand-600 mt-0.5">
                  {founder.role}
                </p>
              </div>

              <p className="text-gray-600 text-sm leading-relaxed text-center mb-6">
                {founder.description}
              </p>

              <div className="border-t border-gray-100 pt-5">
                <p className="text-xs uppercase tracking-wider text-gray-400 font-semibold mb-3">
                  Key Responsibilities
                </p>
                <ul className="space-y-2.5">
                  {founder.responsibilities.map((r) => (
                    <li
                      key={r}
                      className="flex items-start gap-2.5 text-sm text-gray-700"
                    >
                      <CheckCircle2 className="h-4 w-4 text-brand-500 mt-0.5 shrink-0" />
                      {r}
                    </li>
                  ))}
                </ul>
              </div>
            </CardContent>
          </Card>
        </FadeInOnScroll>
      ))}
    </div>
  );
}
