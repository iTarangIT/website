"use client";

import { cn } from "@/lib/utils";
import { callSchedule } from "@/data/portal/leads";

const HOURS = [9, 10, 11, 12, 13, 14, 15, 16, 17];
const DAYS = ["Today", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

const STATUS_STYLES = {
  scheduled: "bg-brand-500/15 text-brand-200 border-brand-500/30",
  "in-progress": "bg-accent-amber/20 text-accent-amber border-accent-amber/40 animate-pulse",
  completed: "bg-accent-green/15 text-accent-green border-accent-green/30",
  missed: "bg-red-500/15 text-red-300 border-red-500/30",
};

export default function CallScheduler() {
  return (
    <section className="rounded-xl bg-white/5 border border-white/10 overflow-hidden">
      <div className="px-5 py-4 border-b border-white/10 flex items-center justify-between">
        <div>
          <h4 className="text-sm font-semibold text-gray-200">AI call scheduler</h4>
          <p className="text-[11px] text-gray-500 mt-0.5">7-day view · click a slot to see lead detail (demo only)</p>
        </div>
        <div className="flex items-center gap-2 text-[10px]">
          <LegendSwatch cls={STATUS_STYLES.scheduled} label="Scheduled" />
          <LegendSwatch cls={STATUS_STYLES["in-progress"]} label="In progress" />
          <LegendSwatch cls={STATUS_STYLES.completed} label="Completed" />
          <LegendSwatch cls={STATUS_STYLES.missed} label="Missed" />
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-[11px]">
          <caption className="sr-only">Upcoming 7-day AI call schedule with per-slot status.</caption>
          <thead className="bg-black/30 text-gray-500">
            <tr>
              <th scope="col" className="text-left px-3 py-2 font-semibold">Day</th>
              {HOURS.map((h) => (
                <th key={h} scope="col" className="text-center px-2 py-2 font-semibold">
                  {h}:00
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {DAYS.map((day, dayIdx) => (
              <tr key={day}>
                <td className="px-3 py-2 font-medium text-gray-200 whitespace-nowrap">{day}</td>
                {HOURS.map((h) => {
                  const slot = callSchedule.find((s) => s.dayOffset === dayIdx && s.hour === h);
                  if (!slot) {
                    return (
                      <td key={h} className="px-1 py-1">
                        <span className="block h-7 rounded bg-white/5 opacity-40" />
                      </td>
                    );
                  }
                  return (
                    <td key={h} className="px-1 py-1">
                      <span
                        className={cn(
                          "block h-7 rounded border text-[9px] font-semibold flex items-center justify-center px-1 truncate",
                          STATUS_STYLES[slot.status],
                        )}
                        title={`${slot.leadName} · ${slot.status}`}
                      >
                        {slot.leadName?.split(" ")[0] ?? slot.status}
                      </span>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function LegendSwatch({ cls, label }: { cls: string; label: string }) {
  return (
    <span className={"inline-flex items-center px-1.5 py-0.5 rounded border font-semibold " + cls}>{label}</span>
  );
}
