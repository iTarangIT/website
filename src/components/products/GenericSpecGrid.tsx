"use client";

import Image from "next/image";
import ProductPlaceholder from "./ProductPlaceholder";

interface SpecItem {
  label: string;
  value: string;
}

interface GenericSpecGridProps {
  title: string;
  subtitle: string;
  specs: SpecItem[];
  image?: string;
  placeholderType?: "battery" | "inverter" | "charger";
}

export default function GenericSpecGrid({ title, subtitle, specs, image, placeholderType = "battery" }: GenericSpecGridProps) {
  return (
    <div className="p-8 md:p-12 bg-white rounded-b-2xl">
      <div className="text-center mb-8">
        <h2 className="font-sans text-2xl md:text-[30px] font-extrabold uppercase tracking-wide text-[#0a2540] mb-3">
          Product <span className="text-brand-600">Specifications</span>
        </h2>
        <p className="text-sm text-[#64748b] leading-relaxed max-w-2xl mx-auto font-sans">
          {subtitle}
        </p>
      </div>

      {/* Center Image */}
      <div className="relative flex justify-center items-center my-10 md:my-12">
        <div className="absolute w-[300px] h-[160px] md:w-[460px] md:h-[240px] rounded-[50%] bg-[radial-gradient(ellipse_at_center,rgba(19,143,198,0.18)_0%,rgba(19,143,198,0.08)_40%,transparent_70%)] top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 pointer-events-none" />
        <div className="absolute w-[260px] h-[130px] md:w-[380px] md:h-[180px] rounded-[50%] border border-brand-500/20 top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 pointer-events-none" />
        {image ? (
          <Image
            src={image}
            alt={title}
            width={260}
            height={260}
            className="relative z-10 w-[200px] h-auto md:w-[260px] object-contain drop-shadow-[0_16px_48px_rgba(19,143,198,0.4)]"
          />
        ) : (
          <ProductPlaceholder type={placeholderType} className="relative z-10 w-[200px] h-[200px] md:w-[260px] md:h-[260px]" />
        )}
      </div>

      {/* Spec Badge */}
      <div className="flex justify-center mb-5">
        <div className="font-sans text-[15px] font-extrabold tracking-[2px] uppercase px-9 py-2.5 rounded-md inline-block bg-[#00d296]/10 text-[#009966] border-[1.5px] border-[#00c48c]/30">
          Core Specifications
        </div>
      </div>

      {/* Spec Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-4xl mx-auto">
        {specs.map((spec) => (
          <div key={spec.label} className="flex items-center gap-3 p-3.5 px-5 bg-[#f8fafc] border border-[#e2e8f4] rounded-lg transition-all duration-250 hover:bg-brand-50 hover:border-brand-300 hover:translate-x-1 group">
            <div className="flex-1 min-w-0">
              <div className="text-[10px] text-[#94a3b8] uppercase tracking-[0.7px] mb-0.5 leading-tight">
                {spec.label}
              </div>
              <div className="font-sans text-[18px] font-bold text-[#0a2540] leading-tight group-hover:text-brand-600 transition-colors">
                {spec.value}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
