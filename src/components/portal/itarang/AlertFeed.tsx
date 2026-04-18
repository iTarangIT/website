import { cn } from "@/lib/utils";
import { controlTowerAlerts } from "@/data/portal/itarang-mock";
import { Thermometer, WifiOff, MapPin, Zap, ShieldAlert, LucideIcon } from "lucide-react";

const TYPE_ICON: Record<string, LucideIcon> = {
  "temp-stress": Thermometer,
  "cell-imbalance": Zap,
  offline: WifiOff,
  "geo-shift": MapPin,
  "default-risk": ShieldAlert,
};

const SEVERITY_STYLES: Record<string, string> = {
  info: "text-brand-300 bg-brand-500/10 border-brand-500/20",
  warning: "text-accent-amber bg-accent-amber/10 border-accent-amber/20",
  critical: "text-red-400 bg-red-500/10 border-red-500/20",
};

export default function AlertFeed() {
  return (
    <section className="rounded-xl bg-white/5 border border-white/10">
      <div className="flex items-center justify-between px-5 py-4 border-b border-white/10">
        <div>
          <h4 className="text-sm font-semibold text-gray-200">Alert Feed</h4>
          <p className="text-xs text-gray-500 mt-0.5">Fleet exceptions — last 6 hours</p>
        </div>
      </div>
      <div className="divide-y divide-white/5">
        {controlTowerAlerts.map((a) => {
          const Icon = TYPE_ICON[a.type] ?? ShieldAlert;
          return (
            <div key={a.id} className="flex items-start gap-3 px-5 py-3">
              <div className={cn("shrink-0 h-8 w-8 rounded-lg flex items-center justify-center border", SEVERITY_STYLES[a.severity])}>
                <Icon className="h-3.5 w-3.5" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-white truncate">{a.title}</p>
                <p className="text-xs text-gray-500 truncate">{a.subtitle}</p>
              </div>
              <div className="shrink-0 text-right">
                <p className="text-[11px] text-gray-400">{a.city}</p>
                <p className="text-[10px] text-gray-500">{a.timeAgo}</p>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
