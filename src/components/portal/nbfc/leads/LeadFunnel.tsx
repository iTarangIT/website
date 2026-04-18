"use client";

import { Funnel, FunnelChart, LabelList, ResponsiveContainer, Tooltip } from "recharts";
import { leadFunnel } from "@/data/portal/leads";
import ChartWithTableFallback from "@/components/portal/shared/ChartWithTableFallback";

const DATA = [
  { name: "Cold", value: leadFunnel.cold, fill: "#5b7bff" },
  { name: "Warm", value: leadFunnel.warm, fill: "#38bdf8" },
  { name: "Hot", value: leadFunnel.hot, fill: "#fbbf24" },
  { name: "Converted", value: leadFunnel.converted, fill: "#10b981" },
];

export default function LeadFunnel() {
  const chart = (
    <div style={{ width: "100%", height: 240 }} role="img" aria-label="Lead conversion funnel chart">
      <ResponsiveContainer>
        <FunnelChart>
          <Tooltip
            contentStyle={{
              background: "#0a0e1a",
              border: "1px solid rgba(255,255,255,0.1)",
              borderRadius: 8,
              color: "white",
              fontSize: 11,
            }}
          />
          <Funnel dataKey="value" data={DATA} isAnimationActive>
            <LabelList position="right" dataKey="name" stroke="none" fill="#cbd5e1" fontSize={11} />
            <LabelList position="center" dataKey="value" stroke="none" fill="white" fontSize={12} fontWeight="bold" />
          </Funnel>
        </FunnelChart>
      </ResponsiveContainer>
    </div>
  );

  const conversions = [
    { from: "Cold → Warm", pct: leadFunnel.coldToWarm },
    { from: "Warm → Hot", pct: leadFunnel.warmToHot },
    { from: "Hot → Converted", pct: leadFunnel.hotToConverted },
  ];

  const table = (
    <div className="rounded-lg border border-white/10 overflow-hidden">
      <table className="w-full text-[11px]">
        <caption className="sr-only">Lead funnel counts and stage-to-stage conversion rates.</caption>
        <thead className="bg-black/30 text-gray-500">
          <tr>
            <th scope="col" aria-sort="none" className="text-left px-3 py-2 font-semibold">Stage</th>
            <th scope="col" aria-sort="none" className="text-right px-3 py-2 font-semibold">Count</th>
            <th scope="col" aria-sort="none" className="text-right px-3 py-2 font-semibold">Conversion to next</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-white/5">
          {DATA.map((d, i) => (
            <tr key={d.name}>
              <td className="px-3 py-1.5 text-white">{d.name}</td>
              <td className="px-3 py-1.5 text-gray-200 tabular-nums text-right">{d.value.toLocaleString("en-IN")}</td>
              <td className="px-3 py-1.5 text-gray-400 tabular-nums text-right">
                {i < conversions.length ? `${conversions[i].pct}%` : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );

  const summary = `${leadFunnel.cold.toLocaleString("en-IN")} cold leads flow through to ${leadFunnel.converted.toLocaleString("en-IN")} converted at a ${leadFunnel.coldToWarm}% / ${leadFunnel.warmToHot}% / ${leadFunnel.hotToConverted}% conversion cascade.`;

  return (
    <section className="rounded-xl bg-white/5 border border-white/10 p-5">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h4 className="text-sm font-semibold text-gray-200">Conversion funnel</h4>
          <p className="text-[11px] text-gray-500 mt-0.5">
            Cold → Converted · {leadFunnel.coldToWarm}% → {leadFunnel.warmToHot}% → {leadFunnel.hotToConverted}%
          </p>
        </div>
      </div>
      <ChartWithTableFallback chart={chart} table={table} summary={summary} />
    </section>
  );
}
