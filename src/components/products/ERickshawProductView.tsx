"use client";

import { useState, useEffect } from "react";
import { eRickshawBatteries } from "@/data/products";
import { getBatterySpecGroups } from "@/data/product-specs-grouped";
import GenericVariantSelector from "./GenericVariantSelector";
import TabHero from "./TabHero";
import SafetyFeatures from "./SafetyFeatures";
import KeyAdvantages from "./KeyAdvantages";
import GroupedSpecDisplay from "./GroupedSpecDisplay";

export default function ERickshawProductView({ initialVariantId }: { initialVariantId?: string | null }) {
  const initial = (initialVariantId && eRickshawBatteries.find((b) => b.id === initialVariantId)) ? initialVariantId : eRickshawBatteries[0].id;
  const [selectedId, setSelectedId] = useState(initial);
  const selected = eRickshawBatteries.find((b) => b.id === selectedId) ?? eRickshawBatteries[0];

  useEffect(() => {
    if (initialVariantId && eRickshawBatteries.find((b) => b.id === initialVariantId)) {
      setSelectedId(initialVariantId);
    }
  }, [initialVariantId]);

  const variants = eRickshawBatteries.map((b) => ({ id: b.id, label: b.label }));

  return (
    <section className="py-12 md:py-20 bg-[#f4f7fb]">
      <div className="mx-auto max-w-[1100px] px-4 sm:px-6 lg:px-8">
        {/* TOP TAB NAVIGATION */}
        <div className="mb-10">
          <GenericVariantSelector
            variants={variants}
            selectedId={selectedId}
            onSelect={setSelectedId}
          />
        </div>

        {/* TAB PANEL CONTAINER */}
        <div className="rounded-2xl overflow-hidden border border-[#dde3ef] bg-white shadow-[0_4px_60px_rgba(10,37,64,0.08)]">
          {/* HERO SECTION */}
          <TabHero battery={selected} />

          {/* SAFETY FEATURES GRID */}
          <div className="border-t border-[#eaeff8]">
            <SafetyFeatures />
          </div>

          {/* WHY CHOOSE US GRID */}
          <div className="border-t border-[#eaeff8]">
            <KeyAdvantages />
          </div>

          {/* GROUPED SPECIFICATIONS */}
          <div className="border-t border-[#eaeff8] bg-white">
            <GroupedSpecDisplay
              title={selected.label}
              subtitle={`Full technical specifications for the iTarang ${selected.label} — engineered for efficiency and long-range performance.`}
              groups={getBatterySpecGroups(selected)}
              image={`/images/${selected.label}.png`}
            />
          </div>
        </div>
      </div>
    </section>
  );
}
