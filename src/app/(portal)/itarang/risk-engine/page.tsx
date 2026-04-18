import ThresholdSlider from "@/components/portal/itarang/risk-engine/ThresholdSlider";
import { defaultThresholds } from "@/data/portal/risk-thresholds";
import DataFreshnessBadge from "@/components/portal/shared/DataFreshnessBadge";

export default function RiskEnginePage() {
  return (
    <div className="px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <header className="flex items-center justify-between gap-3 flex-wrap">
        <div>
          <h1 className="text-2xl font-semibold text-white tracking-tight">Risk Rule Engine</h1>
          <p className="text-sm text-gray-400 mt-1">
            Tune CDS/PCI/EMI/usage thresholds · every change routes through dual approval + MFA + audit
          </p>
        </div>
        <DataFreshnessBadge />
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {defaultThresholds.map((t) => (
          <ThresholdSlider key={t.id} threshold={t} />
        ))}
      </div>

      <p className="text-[10px] text-gray-500 border-t border-white/10 pt-4 leading-relaxed">
        Thresholds govern how the BRD-defined risk formulas classify accounts. Changes do NOT retroactively alter historical CDS/PCI
        scores — they only affect future evaluations. Compliant with RBI Digital Lending Directions 2025.
      </p>
    </div>
  );
}
