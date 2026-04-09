"use client";

import { useState, useEffect } from "react";
import { chargerProducts, chargerFeatures } from "@/data/products";
import { getChargerSpecGroups } from "@/data/product-specs-grouped";
import GenericVariantSelector from "./GenericVariantSelector";
import GenericTabHero from "./GenericTabHero";
import GenericFeatures from "./GenericFeatures";
import GroupedSpecDisplay from "./GroupedSpecDisplay";

export default function ChargerProductView({ initialVariantId }: { initialVariantId?: string | null }) {
  const initial = (initialVariantId && chargerProducts.find((p) => p.id === initialVariantId)) ? initialVariantId : chargerProducts[0].id;
  const [selectedId, setSelectedId] = useState(initial);
  const selected = chargerProducts.find((p) => p.id === selectedId) ?? chargerProducts[0];

  useEffect(() => {
    if (initialVariantId && chargerProducts.find((p) => p.id === initialVariantId)) {
      setSelectedId(initialVariantId);
    }
  }, [initialVariantId]);

  const variants = chargerProducts.map((p) => ({
    id: p.id,
    label: `${p.outputVoltage} ${p.outputCurrent}`,
  }));

  return (
    <section className="py-12 md:py-20 bg-[#f4f7fb]">
      <div className="mx-auto max-w-[1100px] px-4 sm:px-6 lg:px-8">
        <div className="mb-10">
          <GenericVariantSelector
            variants={variants}
            selectedId={selectedId}
            onSelect={setSelectedId}
          />
        </div>

        <div className="rounded-2xl overflow-hidden border border-[#dde3ef] bg-white shadow-[0_4px_60px_rgba(10,37,64,0.08)]">
          <GenericTabHero
            categoryLabel="Smart EV Charger"
            title={`${selected.outputVoltage}`}
            highlight={`${selected.outputCurrent} Charger`}
            tagline={`${selected.efficiency} Efficiency · ${selected.chargingTime}`}
            description={`The ${selected.label} features a CC-CV smart charging algorithm with automatic cutoff for optimal battery health. Compatible with ${selected.compatibility.join(", ")} — built for Indian voltage conditions (${selected.inputVoltage}).`}
            image="/images/charger.png"
            placeholderType="charger"
          />

          <div className="border-t border-[#eaeff8]">
            <GenericFeatures
              title="Smart"
              highlightWord="Charging"
              subtitle="Every iTarang charger is engineered with intelligent safety systems and optimized charging profiles for LiFePO4 batteries."
              features={chargerFeatures}
            />
          </div>

          <div className="border-t border-[#eaeff8] bg-white">
            <GroupedSpecDisplay
              title={selected.label}
              subtitle={`Full technical specifications for the ${selected.label} — designed for fast, safe, and efficient charging.`}
              groups={getChargerSpecGroups(selected)}
              image="/images/charger.png"
              placeholderType="charger"
            />
          </div>
        </div>
      </div>
    </section>
  );
}
