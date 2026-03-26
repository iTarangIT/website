"use client";

import { Star } from "lucide-react";
import { advisors } from "@/data/team";
import FadeInOnScroll from "@/components/shared/FadeInOnScroll";

export default function AdvisoryBoard() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {advisors.map((advisor, idx) => (
        <FadeInOnScroll key={advisor.title} delay={idx * 0.1}>
          <div className="rounded-xl border border-gray-100 bg-gray-50/50 p-6 text-center hover:bg-white hover:shadow-sm transition-all">
            <div className="mx-auto w-12 h-12 rounded-full bg-brand-100 flex items-center justify-center mb-4">
              <Star className="h-5 w-5 text-brand-600" />
            </div>
            <h3 className="text-base font-bold text-gray-900">
              {advisor.title}
            </h3>
            <p className="text-sm text-gray-500 mt-1">{advisor.expertise}</p>
          </div>
        </FadeInOnScroll>
      ))}
    </div>
  );
}
