"use client";

import { Building, Award, MapPin } from "lucide-react";
import { siteConfig } from "@/data/site";
import FadeInOnScroll from "@/components/shared/FadeInOnScroll";

const details = [
  {
    icon: Building,
    label: "Legal Entity",
    value: "iTarang Technologies Private Limited",
    sublabel: "Incorporated under the Companies Act, 2013",
    color: "text-brand-600",
    bg: "bg-brand-50",
  },
  {
    icon: Award,
    label: "DPIIT Recognition",
    value: siteConfig.legal.dpiit,
    sublabel: "Eligible for government startup benefits",
    color: "text-green-600",
    bg: "bg-green-50",
  },
  {
    icon: MapPin,
    label: "Registered Office",
    value: siteConfig.address,
    sublabel: "Gurugram, Haryana",
    color: "text-amber-600",
    bg: "bg-amber-50",
  },
];

export default function CompanyDetails() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {details.map((item, idx) => (
        <FadeInOnScroll key={item.label} delay={idx * 0.12}>
          <div className="rounded-xl border border-gray-100 bg-white p-6 hover:shadow-sm transition-shadow h-full">
            <div
              className={`w-10 h-10 rounded-lg ${item.bg} flex items-center justify-center mb-4`}
            >
              <item.icon className={`h-5 w-5 ${item.color}`} />
            </div>
            <p className="text-xs uppercase tracking-wider text-gray-400 font-semibold mb-1">
              {item.label}
            </p>
            <p className="text-sm font-bold text-gray-900">{item.value}</p>
            <p className="text-xs text-gray-500 mt-1">{item.sublabel}</p>
          </div>
        </FadeInOnScroll>
      ))}
    </div>
  );
}
