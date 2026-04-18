"use client";

import { useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import RiskBucketsHeader from "@/components/portal/nbfc/RiskBucketsHeader";
import AssetFilterBar from "@/components/portal/nbfc/AssetFilterBar";
import AssetCard from "@/components/portal/nbfc/AssetCard";
import AssetDetailSheet from "@/components/portal/nbfc/AssetDetailSheet";
import { portalDrivers, type Driver, type RiskBand } from "@/data/portal/drivers";

export default function NBFCAssetsPage() {
  const searchParams = useSearchParams();
  const initialBand = (searchParams.get("risk") as RiskBand | null) ?? null;

  const [selectedBand, setSelectedBand] = useState<RiskBand | "all">(initialBand ?? "all");
  const [battery, setBattery] = useState("all");
  const [city, setCity] = useState("all");
  const [activeDriver, setActiveDriver] = useState<Driver | null>(null);

  const filtered = useMemo(() => {
    return portalDrivers.filter((d) => {
      if (selectedBand !== "all" && d.risk.riskBand !== selectedBand) return false;
      if (battery !== "all" && d.batteryModelId !== battery) return false;
      if (city !== "all" && d.city !== city) return false;
      return true;
    });
  }, [selectedBand, battery, city]);

  const displayed = filtered.slice(0, 10);

  const bucketSummaries = useMemo(() => {
    const totalDrivers = portalDrivers.length;
    return (["low", "medium", "high"] as RiskBand[]).map((band) => {
      const rows = portalDrivers.filter((d) => d.risk.riskBand === band);
      return {
        band,
        count: rows.length,
        totalDrivers,
        totalOutstanding: rows.reduce((a, d) => a + d.loan.outstanding, 0),
      };
    });
  }, []);

  const reset = () => {
    setSelectedBand("all");
    setBattery("all");
    setCity("all");
  };

  return (
    <div className="px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-white tracking-tight">Assets</h1>
          <p className="text-sm text-gray-400 mt-1">
            Financed batteries classified by NPA risk. Click any asset for driver &amp; battery deep-dive.
          </p>
        </div>
      </div>

      <RiskBucketsHeader buckets={bucketSummaries} selected={selectedBand} onSelect={setSelectedBand} />

      <AssetFilterBar
        battery={battery}
        city={city}
        onBatteryChange={setBattery}
        onCityChange={setCity}
        onReset={reset}
        resultCount={filtered.length}
      />

      {displayed.length === 0 ? (
        <div className="rounded-xl bg-white/5 border border-white/10 p-10 text-center">
          <p className="text-sm text-gray-400">No assets match the current filters.</p>
          <button onClick={reset} className="mt-3 text-xs font-semibold text-brand-300 hover:text-brand-200">
            Reset filters
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-3">
          {displayed.map((driver) => (
            <AssetCard key={driver.id} driver={driver} onClick={() => setActiveDriver(driver)} />
          ))}
        </div>
      )}

      {filtered.length > 10 && (
        <p className="text-center text-xs text-gray-500 pt-2">
          Showing first 10 of {filtered.length} matching assets. Refine filters to narrow further.
        </p>
      )}

      <AssetDetailSheet driver={activeDriver} onClose={() => setActiveDriver(null)} />
    </div>
  );
}
