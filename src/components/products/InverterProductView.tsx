"use client";

import { useState, useEffect } from "react";
import { inverterProducts, inverterFeatures } from "@/data/products";
import { getInverterSpecGroups } from "@/data/product-specs-grouped";
import GenericVariantSelector from "./GenericVariantSelector";
import GenericTabHero from "./GenericTabHero";
import GenericFeatures from "./GenericFeatures";
import GroupedSpecDisplay from "./GroupedSpecDisplay";

export default function InverterProductView({ initialVariantId }: { initialVariantId?: string | null }) {
  const initial = (initialVariantId && inverterProducts.find((p) => p.id === initialVariantId)) ? initialVariantId : inverterProducts[0].id;
  const [selectedId, setSelectedId] = useState(initial);
  const selected = inverterProducts.find((p) => p.id === selectedId) ?? inverterProducts[0];

  useEffect(() => {
    if (initialVariantId && inverterProducts.find((p) => p.id === initialVariantId)) {
      setSelectedId(initialVariantId);
    }
  }, [initialVariantId]);

  const variants = inverterProducts.map((p) => ({
    id: p.id,
    label: `${p.outputWattage / 1000}kW`,
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
            categoryLabel="Pure Sine Wave Inverter"
            title={`${selected.outputWattage / 1000}kW`}
            highlight="Inverter"
            tagline={`${selected.waveform} · ${selected.efficiency} Efficiency`}
            description={`The ${selected.label} delivers clean, stable ${selected.outputVoltage} power for your home and small business. With ${selected.efficiency} efficiency and ${selected.transferTime} transfer time, it ensures uninterrupted backup for fans, lights, refrigerators, and sensitive electronics.`}
            image="/images/invertor.jpeg"
            placeholderType="inverter"
          />

          <div className="border-t border-[#eaeff8]">
            <GenericFeatures
              title="Built-in"
              highlightWord="Features"
              subtitle="Every iTarang inverter is engineered for reliability, efficiency, and safe operation across Indian power conditions."
              features={inverterFeatures}
            />
          </div>

          <div className="border-t border-[#eaeff8] bg-white">
            <GroupedSpecDisplay
              title={selected.label}
              subtitle={`Full technical specifications for the ${selected.label} — optimized for reliable home and commercial backup.`}
              groups={getInverterSpecGroups(selected)}
              image="/images/invertor.jpeg"
              placeholderType="inverter"
            />
          </div>
        </div>
      </div>
    </section>
  );
}
