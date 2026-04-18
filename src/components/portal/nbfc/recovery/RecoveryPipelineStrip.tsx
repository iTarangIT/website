import { recoveryPipeline } from "@/data/portal/auction";
import { Recycle, Wrench, Trash2, CheckCircle2 } from "lucide-react";

export default function RecoveryPipelineStrip() {
  return (
    <section className="rounded-xl bg-white/5 border border-white/10 p-5">
      <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
        <div>
          <h4 className="text-sm font-semibold text-gray-200">Recovery pipeline</h4>
          <p className="text-[11px] text-gray-500 mt-0.5">{recoveryPipeline.total} assets in motion</p>
        </div>
        <div className="flex items-center gap-4 text-xs">
          <Meta label="Value locked" value={`₹${recoveryPipeline.valueLockedCr} Cr`} />
          <Meta label="Est. recovery" value={`₹${recoveryPipeline.estRecoveryLakhs} L`} accent="text-accent-green" />
          <Meta label="Recovery rate" value={`${recoveryPipeline.recoveryRatePct}%`} accent="text-accent-green" />
        </div>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Pipe icon={Recycle} label="Needs inspection" value={recoveryPipeline.needsInspection} color="text-brand-300 bg-brand-500/15" />
        <Pipe icon={Wrench} label="Refurbishable" value={recoveryPipeline.refurbishable} color="text-accent-green bg-accent-green/15" />
        <Pipe icon={Trash2} label="Scrap" value={recoveryPipeline.scrap} color="text-red-300 bg-red-500/15" />
        <Pipe icon={CheckCircle2} label="Resold" value={recoveryPipeline.resold} color="text-accent-amber bg-accent-amber/15" />
      </div>
    </section>
  );
}

function Pipe({ icon: Icon, label, value, color }: { icon: typeof Recycle; label: string; value: number; color: string }) {
  return (
    <div className="rounded-lg bg-black/20 border border-white/10 p-4">
      <div className="flex items-center gap-2 mb-2">
        <span className={"h-8 w-8 rounded-lg flex items-center justify-center " + color}>
          <Icon className="h-4 w-4" />
        </span>
        <p className="text-[10px] uppercase tracking-wider text-gray-500 font-semibold">{label}</p>
      </div>
      <p className="text-2xl font-bold text-white tabular-nums">{value}</p>
    </div>
  );
}

function Meta({ label, value, accent }: { label: string; value: string; accent?: string }) {
  return (
    <div>
      <p className="text-[10px] uppercase tracking-wider text-gray-500">{label}</p>
      <p className={"font-bold tabular-nums " + (accent ?? "text-white")}>{value}</p>
    </div>
  );
}
