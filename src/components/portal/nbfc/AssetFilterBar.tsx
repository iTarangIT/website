"use client";

import { BATTERY_MODEL_OPTIONS } from "@/data/portal/drivers";
import { cities } from "@/data/cities";
import { Filter, RotateCcw } from "lucide-react";

interface Props {
  battery: string;
  city: string;
  onBatteryChange: (v: string) => void;
  onCityChange: (v: string) => void;
  onReset: () => void;
  resultCount: number;
}

export default function AssetFilterBar({
  battery,
  city,
  onBatteryChange,
  onCityChange,
  onReset,
  resultCount,
}: Props) {
  return (
    <div className="flex flex-wrap items-center gap-3 rounded-xl bg-white/5 border border-white/10 px-4 py-3">
      <Filter className="h-4 w-4 text-gray-400" />
      <div className="flex items-center gap-2">
        <label className="text-xs text-gray-400">Battery</label>
        <select
          value={battery}
          onChange={(e) => onBatteryChange(e.target.value)}
          className="bg-white/10 border border-white/10 text-white text-xs rounded-md px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-brand-400"
        >
          {BATTERY_MODEL_OPTIONS.map((opt) => (
            <option key={opt.id} value={opt.id} className="bg-gray-950">
              {opt.label}
            </option>
          ))}
        </select>
      </div>
      <div className="flex items-center gap-2">
        <label className="text-xs text-gray-400">City</label>
        <select
          value={city}
          onChange={(e) => onCityChange(e.target.value)}
          className="bg-white/10 border border-white/10 text-white text-xs rounded-md px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-brand-400"
        >
          <option value="all" className="bg-gray-950">All cities</option>
          {cities.filter((c) => c.status === "active" || (c.batteries && c.batteries > 0)).map((c) => (
            <option key={c.name} value={c.name} className="bg-gray-950">
              {c.name}
            </option>
          ))}
        </select>
      </div>
      <div className="ml-auto flex items-center gap-3">
        <span className="text-xs text-gray-400">
          <span className="text-white font-semibold">{resultCount}</span> assets
        </span>
        <button
          onClick={onReset}
          className="inline-flex items-center gap-1 text-xs text-gray-400 hover:text-white transition-colors"
        >
          <RotateCcw className="h-3 w-3" />
          Reset
        </button>
      </div>
    </div>
  );
}
