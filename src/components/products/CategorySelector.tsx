"use client";

import { Battery, Power, PlugZap } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ProductCategory } from "@/data/products";

const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
  battery: Battery,
  power: Power,
  plug: PlugZap,
};

interface CategorySelectorProps {
  categories: ProductCategory[];
  selectedSlug: string;
  onSelect: (slug: string) => void;
}

export default function CategorySelector({ categories, selectedSlug, onSelect }: CategorySelectorProps) {
  return (
    <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 py-10 bg-[#f4f7fb]">
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {categories.map((cat) => {
          const isActive = cat.slug === selectedSlug;
          const Icon = iconMap[cat.icon] ?? Battery;
          return (
            <button
              key={cat.slug}
              onClick={() => onSelect(cat.slug)}
              className={cn(
                "group relative flex flex-col items-center gap-3 rounded-2xl border-2 p-6 transition-all duration-300 cursor-pointer text-center",
                isActive
                  ? "border-brand-500 bg-brand-50 shadow-lg shadow-brand-500/10"
                  : "border-gray-200 bg-white hover:border-brand-300 hover:shadow-md"
              )}
            >
              <div
                className={cn(
                  "flex h-12 w-12 items-center justify-center rounded-xl transition-colors",
                  isActive ? "bg-brand-500 text-white" : "bg-gray-100 text-gray-500 group-hover:bg-brand-100 group-hover:text-brand-600"
                )}
              >
                <Icon className="h-6 w-6" />
              </div>
              <div>
                <h3
                  className={cn(
                    "text-sm font-bold tracking-wide uppercase transition-colors",
                    isActive ? "text-brand-700" : "text-gray-800 group-hover:text-brand-600"
                  )}
                >
                  {cat.name}
                </h3>
                <p className="mt-1 text-xs text-gray-500 leading-relaxed line-clamp-2">
                  {cat.description}
                </p>
              </div>
              {isActive && (
                <div className="absolute -bottom-px left-1/2 -translate-x-1/2 w-12 h-0.5 bg-brand-500 rounded-full" />
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
