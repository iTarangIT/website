import { Users, PhoneCall, BrainCircuit, ArrowRight } from "lucide-react";

export default function LeadDistributionEngine() {
  return (
    <section className="rounded-xl bg-white/5 border border-white/10 p-5">
      <h4 className="text-sm font-semibold text-gray-200 mb-4">Lead distribution engine</h4>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <Bucket
          accent="bg-accent-green/15 border-accent-green/30 text-accent-green"
          icon={Users}
          title="Hot · 80+"
          route="Ground team"
          body="High intent, budget + timeline. Routed to senior sales for warm handshake within 24 hrs."
        />
        <Bucket
          accent="bg-accent-amber/15 border-accent-amber/30 text-accent-amber"
          icon={PhoneCall}
          title="Warm · 50–79"
          route="Call centre"
          body="Interested but unqualified. AI dialer revisits every 4 days until pricing clarity."
        />
        <Bucket
          accent="bg-brand-500/15 border-brand-500/30 text-brand-200"
          icon={BrainCircuit}
          title="Cold · <50"
          route="AI nurture"
          body="Early funnel. Weekly AI touchpoints with lightweight educational content."
        />
      </div>
    </section>
  );
}

function Bucket({
  accent,
  icon: Icon,
  title,
  route,
  body,
}: {
  accent: string;
  icon: typeof Users;
  title: string;
  route: string;
  body: string;
}) {
  return (
    <div className={"rounded-xl border p-4 " + accent}>
      <div className="flex items-center gap-2 mb-2">
        <Icon className="h-4 w-4" />
        <p className="text-sm font-bold">{title}</p>
      </div>
      <p className="text-[11px] uppercase tracking-wider opacity-70 mb-2 flex items-center gap-1">
        <ArrowRight className="h-3 w-3" /> {route}
      </p>
      <p className="text-xs opacity-80 leading-relaxed">{body}</p>
    </div>
  );
}
