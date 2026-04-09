"use client";

import Image from "next/image";
import type { SpecGroup } from "@/data/product-specs-grouped";
import ProductPlaceholder from "./ProductPlaceholder";
import FadeInOnScroll from "@/components/shared/FadeInOnScroll";

// Only show these 3 groups, in this order
const VISIBLE_GROUPS = ["operating", "mechanical", "electrical"];

const groupColors: Record<string, { pill: string; dot: string; line: string }> = {
  operating:  { pill: "bg-amber-50 text-amber-600 border-amber-200",  dot: "bg-amber-400",  line: "bg-amber-200" },
  mechanical: { pill: "bg-slate-50 text-slate-600 border-slate-200",  dot: "bg-slate-400",  line: "bg-slate-200" },
  electrical: { pill: "bg-blue-50 text-blue-600 border-blue-200",     dot: "bg-blue-400",   line: "bg-blue-200" },
};

interface GroupedSpecDisplayProps {
  title: string;
  subtitle: string;
  groups: SpecGroup[];
  image?: string;
  placeholderType?: "battery" | "inverter" | "charger";
}

/* ── Single spec group rendered with left/right flanking ── */
function SpecSection({ group, colors }: { group: SpecGroup; colors: { pill: string; dot: string; line: string } }) {
  const specs = group.specs.filter((s) => s.value !== null);
  if (specs.length === 0) return null;

  const mid = Math.ceil(specs.length / 2);
  const leftSpecs = specs.slice(0, mid);
  const rightSpecs = specs.slice(mid);

  return (
    <div>
      {/* Group pill badge — centered */}
      <div className="flex justify-center mb-6">
        <span className={`inline-block px-6 py-2 rounded-full text-[13px] font-bold uppercase tracking-[0.1em] border ${colors.pill}`}>
          {group.groupLabel}
        </span>
      </div>

      {/* Desktop: left specs ── (gap) ── right specs */}
      <div className="hidden md:grid md:grid-cols-[1fr_180px_1fr] items-start">
        {/* Left */}
        <div className="flex flex-col gap-5 pr-4">
          {leftSpecs.map((spec) => (
            <div key={spec.label} className="flex items-center gap-3 justify-end text-right">
              <div className="min-w-0">
                <p className="text-[10px] uppercase tracking-[0.08em] text-gray-400 mb-0.5">{spec.label}</p>
                <p className="text-[15px] font-bold text-[#0a2540]">{spec.value}</p>
              </div>
              <div className="flex items-center shrink-0">
                <div className={`w-8 h-[1.5px] ${colors.line}`} />
                <div className={`w-2 h-2 rounded-full ${colors.dot}`} />
              </div>
            </div>
          ))}
        </div>

        {/* Center spacer (image is placed once outside, this aligns with it) */}
        <div />

        {/* Right */}
        <div className="flex flex-col gap-5 pl-4">
          {rightSpecs.map((spec) => (
            <div key={spec.label} className="flex items-center gap-3 text-left">
              <div className="flex items-center shrink-0">
                <div className={`w-2 h-2 rounded-full ${colors.dot}`} />
                <div className={`w-8 h-[1.5px] ${colors.line}`} />
              </div>
              <div className="min-w-0">
                <p className="text-[10px] uppercase tracking-[0.08em] text-gray-400 mb-0.5">{spec.label}</p>
                <p className="text-[15px] font-bold text-[#0a2540]">{spec.value}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Mobile: 2-col grid */}
      <div className="md:hidden grid grid-cols-2 gap-3">
        {specs.map((spec) => (
          <div key={spec.label} className="bg-gray-50 rounded-lg p-3 border border-gray-100">
            <p className="text-[9px] uppercase tracking-[0.08em] text-gray-400 mb-0.5">{spec.label}</p>
            <p className="text-[14px] font-bold text-[#0a2540]">{spec.value}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── Main component ── */
export default function GroupedSpecDisplay({ title, subtitle, groups, image, placeholderType = "battery" }: GroupedSpecDisplayProps) {
  // Filter to only the 3 desired groups, in order
  const visibleGroups = VISIBLE_GROUPS
    .map((key) => groups.find((g) => g.groupKey === key))
    .filter((g): g is SpecGroup => !!g && g.specs.some((s) => s.value !== null));

  if (visibleGroups.length === 0) return null;

  // Split: first group goes above image, rest go below
  const [firstGroup, ...restGroups] = visibleGroups;

  return (
    <div className="py-12 md:py-16 px-4 md:px-8 bg-white rounded-b-2xl overflow-hidden">
      {/* Section header */}
      <FadeInOnScroll>
        <div className="text-center mb-10">
          <h2 className="font-sans text-2xl md:text-[32px] font-extrabold tracking-wide text-[#0a2540]">
            Product <span className="text-brand-600">Specifications</span>
          </h2>
          <p className="text-sm text-[#64748b] leading-relaxed max-w-2xl mx-auto font-sans mt-2">
            {subtitle}
          </p>
        </div>
      </FadeInOnScroll>

      <div className="max-w-5xl mx-auto">
        {/* First group (Operation Conditions) — above the image */}
        <FadeInOnScroll>
          <SpecSection group={firstGroup} colors={groupColors[firstGroup.groupKey] ?? groupColors.operating} />
        </FadeInOnScroll>

        {/* Single centered product image */}
        <FadeInOnScroll>
          <div className="relative flex justify-center items-center my-10 md:my-14">
            <div className="absolute w-[280px] h-[150px] md:w-[400px] md:h-[220px] rounded-[50%] bg-[radial-gradient(ellipse_at_center,rgba(19,143,198,0.14)_0%,rgba(19,143,198,0.05)_45%,transparent_70%)] top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 pointer-events-none" />
            {image ? (
              <Image
                src={image}
                alt={title}
                width={280}
                height={280}
                className="relative z-10 w-[200px] h-auto md:w-[260px] object-contain drop-shadow-[0_12px_40px_rgba(19,143,198,0.3)]"
              />
            ) : (
              <ProductPlaceholder type={placeholderType} className="relative z-10 w-[180px] h-[180px] md:w-[240px] md:h-[240px]" />
            )}
          </div>
        </FadeInOnScroll>

        {/* Remaining groups (Mechanical, Electrical) — below the image */}
        <div className="space-y-14">
          {restGroups.map((group) => (
            <FadeInOnScroll key={group.groupKey}>
              <SpecSection group={group} colors={groupColors[group.groupKey] ?? groupColors.electrical} />
            </FadeInOnScroll>
          ))}
        </div>
      </div>
    </div>
  );
}
