"use client";

import { cn } from "@/lib/utils";
import type { ERickshawBattery } from "@/data/products";

interface VariantSelectorProps {
  variants: ERickshawBattery[];
  selectedId: string;
  onSelect: (id: string) => void;
}

export default function VariantSelector({ variants, selectedId, onSelect }: VariantSelectorProps) {
  return (
    <div className="flex flex-wrap items-center justify-center gap-2 md:gap-3 p-4">
      {variants.map((variant) => {
        const isSelected = variant.id === selectedId;
        return (
          <button
            key={variant.id}
            onClick={() => onSelect(variant.id)}
            className={cn(
              "px-5 py-2.5 rounded text-sm font-bold tracking-wider uppercase transition-all duration-200 cursor-pointer border",
              isSelected
                ? "bg-[#ef6c00] text-white border-[#ef6c00] shadow-md shadow-orange-500/30"
                : "bg-[#f4f6fa] text-slate-500 border-slate-200 hover:bg-[#eaf0ff] hover:text-brand-600 hover:border-brand-300"
            )}
          >
            {variant.voltage}V · {variant.capacity}AH
          </button>
        );
      })}
    </div>
  );
}
