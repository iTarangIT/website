"use client";

import { useState } from "react";
import { eRickshawBatteries } from "@/data/products";
import VariantSelector from "./VariantSelector";
import TabHero from "./TabHero";
import SafetyFeatures from "./SafetyFeatures";
import KeyAdvantages from "./KeyAdvantages";
import SpecsSpotlight from "./SpecsSpotlight";

export default function ERickshawProductView() {
  const [selectedId, setSelectedId] = useState(eRickshawBatteries[0].id);
  const selected = eRickshawBatteries.find((b) => b.id === selectedId) ?? eRickshawBatteries[0];

  return (
    <section className="py-12 md:py-20 bg-[#f4f7fb]">
      <div className="mx-auto max-w-[1100px] px-4 sm:px-6 lg:px-8">
        {/* TOP TAB NAVIGATION */}
        <div className="mb-10">
          <VariantSelector
            variants={eRickshawBatteries}
            selectedId={selectedId}
            onSelect={setSelectedId}
          />
        </div>

        {/* TAB PANEL CONTAINER (Matches HTML .page border-radius and shadow) */}
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

          {/* SPECS SPOTLIGHT GRID */}
          <div className="border-t border-[#eaeff8] bg-white">
            <SpecsSpotlight battery={selected} />
          </div>
        </div>
      </div>
    </section>
  );
}
