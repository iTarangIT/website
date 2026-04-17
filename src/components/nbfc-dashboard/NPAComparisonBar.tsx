export default function NPAComparisonBar({
  itarang,
  industry,
}: {
  itarang: number;
  industry: number;
}) {
  const maxValue = Math.max(itarang, industry, 0);
  const scale = maxValue === 0 ? 1 : maxValue * 1.25;
  const toPct = (v: number) => Math.max(0, Math.min(100, (v / scale) * 100));
  const pctITarang = toPct(itarang);
  const pctIndustry = toPct(industry);

  return (
    <div className="space-y-3">
      <div>
        <div className="flex items-center justify-between text-[11px] font-semibold">
          <span className="text-gray-600">iTarang portfolio</span>
          <span className="text-accent-green">{itarang.toFixed(1)}%</span>
        </div>
        <div className="mt-1 h-2 w-full rounded-full bg-gray-100 overflow-hidden">
          <div
            className="h-full bg-accent-green transition-[width] duration-700"
            style={{ width: `${pctITarang}%` }}
          />
        </div>
      </div>
      <div>
        <div className="flex items-center justify-between text-[11px] font-semibold">
          <span className="text-gray-400">Industry avg.</span>
          <span className="text-accent-amber">{industry.toFixed(1)}%</span>
        </div>
        <div className="mt-1 h-2 w-full rounded-full bg-gray-100 overflow-hidden">
          <div
            className="h-full bg-accent-amber/80 transition-[width] duration-700"
            style={{ width: `${pctIndustry}%` }}
          />
        </div>
      </div>
    </div>
  );
}
