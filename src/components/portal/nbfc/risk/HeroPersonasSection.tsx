import Link from "next/link";
import { ShieldCheck, AlertOctagon, ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { heroPersonas } from "@/data/portal/portfolio";

const CARDS = [
  {
    ...heroPersonas.rajesh,
    tint: "border-accent-green/30 bg-accent-green/5",
    label: "Reliable payer archetype",
    icon: ShieldCheck,
    iconCls: "text-accent-green",
  },
  {
    ...heroPersonas.mohan,
    tint: "border-red-500/30 bg-red-500/5",
    label: "At-risk archetype",
    icon: AlertOctagon,
    iconCls: "text-red-300",
  },
];

export default function HeroPersonasSection() {
  return (
    <section className="rounded-xl bg-white/5 border border-white/10 p-5">
      <h4 className="text-sm font-semibold text-gray-200 mb-1">Two borrowers, two stories</h4>
      <p className="text-[11px] text-gray-500 mb-4">Representative accounts · click to open Case Workspace in Battery Monitoring</p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {CARDS.map((p) => {
          const Icon = p.icon;
          return (
            <Link
              key={p.id}
              href={`/nbfc/batteries?case=${p.id}`}
              className={cn("group rounded-xl border p-4 transition-colors hover:brightness-110", p.tint)}
            >
              <div className="flex items-center gap-2 mb-3">
                <Icon className={cn("h-4 w-4 shrink-0", p.iconCls)} />
                <p className={cn("text-[10px] uppercase tracking-wider font-bold", p.iconCls)}>{p.label}</p>
                <ArrowRight className="h-3 w-3 ml-auto text-gray-500 group-hover:translate-x-0.5 transition-transform" />
              </div>
              <p className="text-base font-bold text-white">{p.name}</p>
              <p className="text-[11px] text-gray-400 mb-3">
                {p.batteryId} · {p.city} · {p.dealer}
              </p>
              <dl className="grid grid-cols-2 gap-x-3 gap-y-1.5 text-[11px]">
                <dt className="text-gray-500">SOH</dt>
                <dd className="text-gray-200 text-right tabular-nums">{p.sohPct}%</dd>
                <dt className="text-gray-500">Daily KM</dt>
                <dd className="text-gray-200 text-right tabular-nums">
                  {p.dailyKm}
                  {p.dailyKm !== p.previousDailyKm && (
                    <span className="text-gray-500"> (was {p.previousDailyKm})</span>
                  )}
                </dd>
                <dt className="text-gray-500">EMI overdue</dt>
                <dd className={cn("text-right tabular-nums", p.emiOverdueDays > 0 ? "text-red-300" : "text-accent-green")}>
                  {p.emiOverdueDays === 0 ? "On time" : `${p.emiOverdueDays}d`}
                </dd>
                <dt className="text-gray-500">CDS</dt>
                <dd className={cn("text-right tabular-nums font-bold", p.cds > 60 ? "text-red-300" : p.cds > 40 ? "text-accent-amber" : "text-accent-green")}>{p.cds}</dd>
                <dt className="text-gray-500">PCI</dt>
                <dd className={cn("text-right tabular-nums font-bold", p.pci < 0.5 ? "text-red-300" : p.pci < 0.75 ? "text-accent-amber" : "text-accent-green")}>{p.pci.toFixed(2)}</dd>
                <dt className="text-gray-500">Status</dt>
                <dd className={cn("text-right text-[10px] uppercase tracking-wider font-bold", p.status === "ACTIVE" ? "text-accent-green" : "text-red-300")}>
                  {p.status}
                </dd>
              </dl>
            </Link>
          );
        })}
      </div>
    </section>
  );
}
