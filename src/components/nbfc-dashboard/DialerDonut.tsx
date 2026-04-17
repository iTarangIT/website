"use client";

import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";
import { dialerStats } from "@/lib/nbfc-mock-data";

// callsMade is the aggregate; the three outcomes below partition it.
// Keep callsMade for the donut's centre total and plot only the outcomes.
const data = [
  { name: "Qualified", value: dialerStats.qualified, color: "#10b981" },
  { name: "Hot Leads", value: dialerStats.hotLeads, color: "#f59e0b" },
  { name: "Disqualified", value: dialerStats.disqualified, color: "#94a3b8" },
];

export default function DialerDonut() {
  const total = dialerStats.callsMade;

  return (
    <div className="rounded-2xl bg-white border border-gray-100 shadow-sm p-6">
      <div className="flex items-start justify-between mb-4 flex-wrap gap-2">
        <div>
          <h3 className="text-base font-semibold text-gray-900">
            Today&apos;s AI Dialer Activity
          </h3>
          <p className="text-xs text-gray-500 mt-0.5">
            Live calls placed by the iTarang qualification agent.
          </p>
        </div>
        <span className="inline-flex items-center gap-1.5 rounded-full bg-green-50 px-2.5 py-1 text-[11px] font-semibold text-accent-green">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-accent-green/70" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-accent-green" />
          </span>
          Live
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 items-center gap-6">
        <div className="relative h-64">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={90}
                paddingAngle={2}
                stroke="none"
              >
                {data.map((entry) => (
                  <Cell key={entry.name} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  background: "rgba(17, 24, 39, 0.92)",
                  border: "none",
                  borderRadius: 8,
                  fontSize: 12,
                  color: "#fff",
                }}
                itemStyle={{ color: "#fff" }}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
            <p className="text-[10px] font-semibold uppercase tracking-widest text-gray-400">
              Calls today
            </p>
            <p className="text-3xl font-semibold text-gray-900 tabular-nums">{total}</p>
          </div>
        </div>

        <ul className="space-y-2">
          {data.map((slice) => (
            <li
              key={slice.name}
              className="flex items-center justify-between rounded-lg border border-gray-100 bg-gray-50/50 px-3 py-2"
            >
              <div className="flex items-center gap-2.5">
                <span
                  className="h-2.5 w-2.5 rounded-full shrink-0"
                  style={{ backgroundColor: slice.color }}
                />
                <span className="text-sm text-gray-700">{slice.name}</span>
              </div>
              <span className="text-sm font-semibold text-gray-900 tabular-nums">
                {slice.value}
              </span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
