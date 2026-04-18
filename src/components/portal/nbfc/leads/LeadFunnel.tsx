"use client";

import { Funnel, FunnelChart, LabelList, ResponsiveContainer, Tooltip } from "recharts";
import { leadFunnel } from "@/data/portal/leads";

const DATA = [
  { name: "Cold", value: leadFunnel.cold, fill: "#5b7bff" },
  { name: "Warm", value: leadFunnel.warm, fill: "#38bdf8" },
  { name: "Hot", value: leadFunnel.hot, fill: "#fbbf24" },
  { name: "Converted", value: leadFunnel.converted, fill: "#10b981" },
];

export default function LeadFunnel() {
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
      <div style={{ width: "100%", height: 240 }}>
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
      <p className="sr-only">
        Funnel: {leadFunnel.cold} cold leads, {leadFunnel.warm} warm, {leadFunnel.hot} hot, {leadFunnel.converted} converted.
      </p>
    </section>
  );
}
