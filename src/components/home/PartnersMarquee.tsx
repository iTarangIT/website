"use client";

import Image from "next/image";
import FadeInOnScroll from "@/components/shared/FadeInOnScroll";
import { cn } from "@/lib/utils";

/** Cards per marquee half. The logo set is repeated up to this many cards so the
 *  track is wider than any viewport — otherwise the loop shows a gap on the reset. */
const MARQUEE_MIN_CARDS = 8;
/** Seconds a single card takes to cross the strip. Higher = calmer drift. */
const MARQUEE_SECONDS_PER_CARD = 4.5;

/** Logo heights are set per-partner, not shared. These marks range from 1.06:1
 *  (Taru) to 6.1:1 (BatteryPool); a single height would let the wide wordmarks
 *  dominate the row and shrink the round marks to nothing. Each height below keeps
 *  the rendered width inside the card's 154px content box (w-[210px] less px-7),
 *  and the stacked lockups sit at h-14 so their wordmark still reads at a glance. */
const partners = [
  {
    name: "BatteryPool",
    src: "/logos/battery_pool_logo.svg",
    width: 189,
    height: 31,
    logoHeight: "h-6",
  },
  {
    name: "Bajaj Finserv",
    src: "/logos/bajaj-finserv.png",
    width: 736,
    height: 200,
    logoHeight: "h-9",
  },
  {
    name: "Trontek",
    src: "/logos/trontek.png",
    width: 759,
    height: 489,
    logoHeight: "h-12",
  },
  {
    name: "NavPrakriti",
    src: "/logos/navprakriti.png",
    width: 670,
    height: 443,
    logoHeight: "h-14",
  },
  {
    name: "Taru Investment Agencies",
    src: "/logos/taru.png",
    width: 374,
    height: 352,
    logoHeight: "h-14",
  },
];

const marqueeHalf = Array.from(
  { length: Math.ceil(MARQUEE_MIN_CARDS / partners.length) },
  () => partners,
).flat();
const marqueeDuration = `${Math.round(marqueeHalf.length * MARQUEE_SECONDS_PER_CARD)}s`;

export default function PartnersMarquee() {
  return (
    // bg-surface-warm is load-bearing: the hero ends with a gradient fading into
    // this exact colour, so any other background leaves a visible seam.
    <section
      aria-label="Our partners"
      className="py-16 md:py-20 bg-surface-warm relative"
    >
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <FadeInOnScroll>
          {/* Eyebrow only — a full heading here would compete with the hero
              headline above and the Lifecycle heading immediately below. */}
          <p className="text-center text-sm font-semibold text-brand-500 tracking-widest uppercase">
            Our Partners
          </p>
          <p className="mt-4 text-center text-base text-gray-500 leading-relaxed max-w-xl mx-auto">
            Building India&rsquo;s battery ecosystem alongside manufacturers,
            financiers, and energy networks.
          </p>

          <div
            style={{ "--marquee-duration": marqueeDuration } as React.CSSProperties}
            className={cn(
              "group/marquee relative mt-10 w-full overflow-hidden py-3",
              "[mask-image:linear-gradient(to_right,transparent,#000_7%,#000_93%,transparent)]",
            )}
          >
            {/* Track holds the set twice; the keyframe travels 50% so the seam is
                invisible. Card spacing MUST come from per-card margins — a flex
                gap sits outside the halves and knocks the loop out of register. */}
            <div
              className={cn(
                "marquee-track flex w-max items-center animate-marquee-reverse",
                "group-hover/marquee:[animation-play-state:paused]",
              )}
            >
              {[...marqueeHalf, ...marqueeHalf].map((partner, i) => {
                const isRepeat = i >= partners.length;
                return (
                  <div
                    key={`${partner.name}-${i}`}
                    // Everything past the first set is padding for the loop —
                    // hidden from AT, and dropped under reduced motion.
                    aria-hidden={isRepeat}
                    className={cn(
                      isRepeat && "marquee-repeat",
                      "group/logo mx-2 sm:mx-3 flex h-24 w-[210px] shrink-0 items-center justify-center",
                      "rounded-2xl bg-gradient-to-br from-white to-surface-warm px-7",
                      "border border-gray-200/60 shadow-sm",
                      "transition-all duration-300 hover:-translate-y-1 hover:border-brand-200 hover:shadow-lg",
                    )}
                  >
                    <Image
                      src={partner.src}
                      alt={partner.name}
                      width={partner.width}
                      height={partner.height}
                      loading="lazy"
                      // Brand colours, no grayscale filter — the row is meant to
                      // show the partner marks as they actually look.
                      className={cn(
                        "w-auto max-w-full object-contain",
                        partner.logoHeight,
                        "transition-transform duration-300 group-hover/logo:scale-105",
                      )}
                    />
                  </div>
                );
              })}
            </div>
          </div>
        </FadeInOnScroll>
      </div>
    </section>
  );
}
