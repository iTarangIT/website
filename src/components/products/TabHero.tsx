"use client";

import Image from "next/image";
import type { ERickshawBattery } from "@/data/products";

export default function TabHero({ battery }: { battery: ERickshawBattery }) {
    // Use a fallback description if not present, similar to the HTML mockup
    const fallbackDesc = `The iTarang ${battery.label} lithium battery offers highest capacity and best-in-efficiency long distance range. With 2,000+ cycles, it ensures fewer charging cycles and continuous output for uninterrupted operations.`;

    return (
        <div className="relative p-8 md:p-12 flex flex-col-reverse md:flex-row items-center justify-between gap-8 overflow-hidden bg-gradient-to-br from-brand-950 to-brand-800 rounded-t-2xl">
            {/* Background ambient glow matching HTML pseudo-elements */}
            <div className="absolute -top-10 -right-10 w-[500px] h-[500px] bg-[radial-gradient(circle,rgba(33,150,243,0.15)_0%,transparent_70%)] pointer-events-none" />

            {/* Bottom glowing border matching HTML */}
            <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-brand-500 to-transparent" />

            {/* Hero Text Content (Left) */}
            <div className="flex-1 min-w-0 z-10 w-full">
                <div className="inline-flex items-center gap-2 font-sans font-bold text-xs tracking-[0.2em] uppercase text-[#ef6c00] mb-3">
                    <div className="w-6 h-[2px] bg-[#ef6c00]" />
                    E-Rickshaw Lithium Battery
                </div>

                <h1 className="font-sans text-4xl md:text-[50px] font-black leading-[1.05] text-white uppercase mt-1">
                    {battery.voltage}V <span className="text-[#ef6c00] block">{battery.capacity}Ah</span>
                </h1>

                <div className="mt-3 inline-block bg-[#2196F3]/10 border border-[#2196F3]/30 rounded px-3.5 py-1 font-sans text-[13px] font-bold tracking-wider text-brand-400 uppercase">
                    {battery.energy} · {battery.chemistry}
                </div>

                <p className="mt-4 text-sm leading-relaxed text-white/70 max-w-[400px]">
                    {fallbackDesc}
                </p>
            </div>

            {/* Hero Image / Icon (Right) */}
            <div className="shrink-0 w-[240px] md:w-[320px] aspect-square flex items-center justify-center relative z-10 transition-transform duration-400 hover:-translate-y-2 hover:scale-105 group">
                <Image
                    src={`/images/${battery.label}.png`}
                    alt={`iTarang ${battery.label} Battery`}
                    width={320}
                    height={320}
                    className="relative z-10 w-full h-auto object-contain drop-shadow-[0_12px_40px_rgba(33,150,243,0.5)] group-hover:drop-shadow-[0_20px_56px_rgba(33,150,243,0.65)] transition-all duration-400"
                />
            </div>
        </div>
    );
}
