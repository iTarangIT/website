import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { threeActStrip } from "@/data/portal/portfolio";

export default function ThreeActStrip() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {threeActStrip.map((act) => (
        <Link
          key={act.act}
          href={act.href}
          className="group rounded-xl bg-white/5 border border-white/10 p-5 hover:bg-white/10 hover:border-brand-500/30 transition-all"
        >
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-2 mb-3">
                <span className="text-2xl leading-none">{act.icon}</span>
                <span className="text-[11px] uppercase tracking-wider font-bold text-gray-400">{act.title}</span>
              </div>
              <p className="text-lg font-semibold text-white mb-1">{act.headline}</p>
              <p className="text-xs text-gray-400">{act.metric}</p>
            </div>
            <ArrowRight className="h-4 w-4 text-gray-500 group-hover:text-brand-300 group-hover:translate-x-0.5 transition-all" />
          </div>
        </Link>
      ))}
    </div>
  );
}
