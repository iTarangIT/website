"use client";

import { Battery, ChevronRight } from "lucide-react";
import Link from "next/link";
import { GridPattern } from "@/components/ui/grid-pattern";
import { cn } from "@/lib/utils";

interface ProductHeroProps {
  title: string;
  subtitle: string;
  breadcrumb?: { label: string; href: string }[];
}

export default function ProductHero({ title, subtitle, breadcrumb }: ProductHeroProps) {
  return (
    <section className="relative overflow-hidden bg-brand-950 pt-28 pb-16 md:pt-32 md:pb-20">
      {/* Background layers */}
      <div className="absolute inset-0 bg-gradient-to-br from-brand-950 via-brand-900/90 to-brand-950" />
      <div className="absolute -top-40 -right-40 w-[500px] h-[500px] rounded-full bg-brand-500/10 blur-[120px]" />
      <div className="absolute -bottom-20 -left-20 w-[300px] h-[300px] rounded-full bg-accent-sky/5 blur-[80px]" />

      <GridPattern
        width={48}
        height={48}
        squares={[
          [4, 4], [8, 2], [12, 6], [16, 3],
        ]}
        className={cn(
          "fill-brand-400/5 stroke-brand-400/8",
          "[mask-image:radial-gradient(600px_circle_at_70%_40%,white,transparent)]",
        )}
      />

      <div className="relative z-10 mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Breadcrumb */}
        {breadcrumb && (
          <nav className="flex items-center gap-1.5 text-sm text-brand-300/60 mb-6 font-sans">
            <Link href="/" className="hover:text-brand-200 transition-colors">Home</Link>
            {breadcrumb.map((item, i) => (
              <span key={item.href} className="flex items-center gap-1.5">
                <ChevronRight className="h-3.5 w-3.5" />
                {i === breadcrumb.length - 1 ? (
                  <span className="text-brand-200">{item.label}</span>
                ) : (
                  <Link href={item.href} className="hover:text-brand-200 transition-colors">
                    {item.label}
                  </Link>
                )}
              </span>
            ))}
          </nav>
        )}

        <div className="mb-6">
          <h1 className="text-3xl md:text-4xl lg:text-5xl font-bold text-white tracking-tight">
            {title}
          </h1>
        </div>

        <p className="text-lg md:text-xl text-brand-200/70 max-w-2xl leading-relaxed font-sans">
          {subtitle}
        </p>
      </div>
    </section>
  );
}
