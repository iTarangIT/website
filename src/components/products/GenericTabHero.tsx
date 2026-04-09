"use client";

import Image from "next/image";
import ProductPlaceholder from "./ProductPlaceholder";

interface GenericTabHeroProps {
  categoryLabel: string;
  title: string;
  highlight: string;
  tagline: string;
  description: string;
  image?: string;
  placeholderType: "battery" | "inverter" | "charger";
}

export default function GenericTabHero({
  categoryLabel,
  title,
  highlight,
  tagline,
  description,
  image,
  placeholderType,
}: GenericTabHeroProps) {
  return (
    <div className="relative p-8 md:p-12 flex flex-col-reverse md:flex-row items-center justify-between gap-8 overflow-hidden bg-gradient-to-br from-brand-950 to-brand-800 rounded-t-2xl">
      {/* Background ambient glow */}
      <div className="absolute -top-10 -right-10 w-[500px] h-[500px] bg-[radial-gradient(circle,rgba(19,143,198,0.15)_0%,transparent_70%)] pointer-events-none" />

      {/* Bottom glowing border */}
      <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-brand-500 to-transparent" />

      {/* Text Content (Left) */}
      <div className="flex-1 min-w-0 z-10 w-full">
        <div className="inline-flex items-center gap-2 font-sans font-bold text-xs tracking-[0.2em] uppercase text-brand-400 mb-3">
          <div className="w-6 h-[2px] bg-brand-400" />
          {categoryLabel}
        </div>

        <h1 className="font-sans text-3xl md:text-[44px] font-black leading-[1.1] text-white uppercase mt-1">
          {title} <span className="text-brand-300 block">{highlight}</span>
        </h1>

        <div className="mt-3 inline-block bg-brand-500/10 border border-brand-500/30 rounded px-3.5 py-1 font-sans text-[13px] font-bold tracking-wider text-brand-300 uppercase">
          {tagline}
        </div>

        <p className="mt-4 text-sm leading-relaxed text-white/70 max-w-[400px]">
          {description}
        </p>
      </div>

      {/* Image / Placeholder (Right) */}
      <div className="shrink-0 w-[240px] md:w-[320px] aspect-square flex items-center justify-center relative z-10">
        {image ? (
          <Image
            src={image}
            alt={`${title} ${highlight}`}
            width={320}
            height={320}
            className="relative z-10 w-full h-auto object-contain drop-shadow-[0_12px_40px_rgba(19,143,198,0.5)]"
          />
        ) : (
          <ProductPlaceholder type={placeholderType} className="w-full h-full" />
        )}
      </div>
    </div>
  );
}
