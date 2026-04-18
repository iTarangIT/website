import { cn } from "@/lib/utils";
import { dealerServiceTickets } from "@/data/portal/dealer-mock";
import { Wrench, Clock } from "lucide-react";

const PRIORITY_COLOR: Record<string, string> = {
  Critical: "bg-red-500/20 text-red-400 border-red-500/30",
  High: "bg-accent-amber/20 text-accent-amber border-accent-amber/30",
  Medium: "bg-brand-500/20 text-brand-300 border-brand-500/30",
  Low: "bg-white/10 text-gray-300 border-white/20",
};

function slaChip(hours: number) {
  if (hours < 2) return "bg-red-500/20 text-red-400";
  if (hours < 6) return "bg-accent-amber/20 text-accent-amber";
  return "bg-accent-green/20 text-accent-green";
}

export default function ServiceQueuePreview() {
  return (
    <section className="rounded-xl bg-white/5 border border-white/10">
      <div className="flex items-center justify-between px-5 py-4 border-b border-white/10">
        <div>
          <h4 className="text-sm font-semibold text-gray-200">Service queue</h4>
          <p className="text-xs text-gray-500 mt-0.5">Open tickets · SLA countdown</p>
        </div>
        <Wrench className="h-4 w-4 text-gray-500" />
      </div>
      <div className="divide-y divide-white/5">
        {dealerServiceTickets.map((t) => (
          <div key={t.id} className="flex items-center justify-between gap-3 px-5 py-3">
            <div className="min-w-0">
              <p className="text-sm font-medium text-white truncate">{t.id} · {t.consumer}</p>
              <p className="text-[11px] text-gray-500 truncate">{t.battery} · {t.issue}</p>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <span className={cn("inline-flex items-center px-2 py-0.5 rounded-full border text-[10px] font-bold tracking-wider", PRIORITY_COLOR[t.priority])}>
                {t.priority.toUpperCase()}
              </span>
              <span className={cn("inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold tabular-nums", slaChip(t.slaRemainingHours))}>
                <Clock className="h-2.5 w-2.5" />
                {t.slaRemainingHours < 1
                  ? `${Math.round(t.slaRemainingHours * 60)}m`
                  : `${t.slaRemainingHours.toFixed(1)}h`}
              </span>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
