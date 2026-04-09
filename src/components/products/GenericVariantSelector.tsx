"use client";

import { cn } from "@/lib/utils";

interface VariantOption {
  id: string;
  label: string;
}

interface GenericVariantSelectorProps {
  variants: VariantOption[];
  selectedId: string;
  onSelect: (id: string) => void;
}

export default function GenericVariantSelector({ variants, selectedId, onSelect }: GenericVariantSelectorProps) {
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
                ? "bg-brand-600 text-white border-brand-600 shadow-md shadow-brand-500/30"
                : "bg-[#f4f6fa] text-slate-500 border-slate-200 hover:bg-brand-50 hover:text-brand-600 hover:border-brand-300"
            )}
          >
            {variant.label}
          </button>
        );
      })}
    </div>
  );
}
