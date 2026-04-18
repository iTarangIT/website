"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { Clock, PauseCircle, Check, XCircle, Settings2 } from "lucide-react";
import { useCountdown } from "@/lib/auction-clock";
import type { AuctionLot } from "@/data/portal/auction";
import DualApprovalModal from "@/components/portal/shared/DualApprovalModal";

interface Props {
  lot: AuctionLot;
}

type PendingAction =
  | { kind: "extend"; minutes: number }
  | { kind: "reduce"; minutes: number }
  | { kind: "pause" }
  | { kind: "end-now" }
  | { kind: "reserve"; value: number }
  | { kind: "approve-winner" }
  | { kind: "cancel" };

function actionSummary(a: PendingAction, lot: AuctionLot) {
  switch (a.kind) {
    case "extend":
      return { title: "Extend auction time", desc: `Add ${a.minutes} minutes to lot ${lot.id}`, audit: "auction-time-extended" as const, label: `Extend +${a.minutes}m`, before: `T-${lot.endsAtIsoOffsetMinutes}m`, after: `T-${lot.endsAtIsoOffsetMinutes + a.minutes}m` };
    case "reduce":
      return { title: "Reduce auction time", desc: `Remove ${a.minutes} minutes from lot ${lot.id}`, audit: "auction-time-reduced" as const, label: `Reduce -${a.minutes}m`, before: `T-${lot.endsAtIsoOffsetMinutes}m`, after: `T-${Math.max(0, lot.endsAtIsoOffsetMinutes - a.minutes)}m` };
    case "pause":
      return { title: "Pause auction", desc: `Pause lot ${lot.id} pending review`, audit: "auction-paused" as const, label: "Pause auction" };
    case "end-now":
      return { title: "End auction now", desc: `Close lot ${lot.id} immediately`, audit: "auction-time-reduced" as const, label: "End now", before: `T-${lot.endsAtIsoOffsetMinutes}m`, after: "T-0" };
    case "reserve":
      return { title: "Set reserve price", desc: `Apply reserve price to lot ${lot.id}`, audit: "reserve-price-set" as const, label: "Reserve price", after: `₹${a.value.toLocaleString("en-IN")}` };
    case "approve-winner":
      return { title: "Approve winning bid", desc: `Close lot ${lot.id} with current top bidder`, audit: "winning-bid-approved" as const, label: "Approve winner", after: `₹${lot.currentBid.toLocaleString("en-IN")}` };
    case "cancel":
      return { title: "Cancel auction", desc: `Withdraw lot ${lot.id} from marketplace`, audit: "auction-cancelled" as const, label: "Cancel auction" };
  }
}

export default function LotAdminControls({ lot }: Props) {
  const [pending, setPending] = useState<PendingAction | null>(null);
  const [reserveInput, setReserveInput] = useState<number>(Math.round(lot.basePrice * 1.15));
  const { formatted, expired } = useCountdown(lot.endsAtIsoOffsetMinutes);

  const summary = pending ? actionSummary(pending, lot) : null;

  return (
    <>
      <article className="rounded-xl bg-white/5 border border-white/10 p-4 space-y-3">
        <div className="flex items-start justify-between gap-2">
          <div>
            <p className="text-xs font-mono text-gray-500">{lot.id}</p>
            <p className="text-sm font-bold text-white">{lot.capacity} · {lot.quantity} units</p>
            <p className="text-[11px] text-gray-400">{lot.modelMix}</p>
          </div>
          <span className={cn(
            "inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider",
            lot.status === "closing-soon" ? "text-accent-amber animate-pulse" : "text-accent-green",
          )}>
            <span className="h-1.5 w-1.5 rounded-full bg-current" />
            {lot.status.replace("-", " ")}
          </span>
        </div>

        <div className="grid grid-cols-2 gap-2 text-[11px]">
          <Tile label="Current bid" value={`₹${lot.currentBid.toLocaleString("en-IN")}`} accent />
          <Tile label="Time remaining" value={expired ? "Ended" : formatted} icon={Clock} warn={!expired && lot.status === "closing-soon"} />
          <Tile label={`Bids · ${lot.bidderCount} bidders`} value={String(lot.bidHistory.length)} />
          <Tile label="Bid velocity" value={`${computeVelocity(lot)}/hr`} />
          <Tile
            label="Expected closing"
            value={formatExpectedClosing(lot.endsAtIsoOffsetMinutes)}
            warn={lot.endsAtIsoOffsetMinutes < 60}
          />
          <Tile
            label="Reserve status"
            value={lot.currentBid >= lot.basePrice * 1.15 ? "Met" : "Below reserve"}
            accent={lot.currentBid >= lot.basePrice * 1.15}
          />
        </div>

        <div className="space-y-1.5">
          <AdminRow label="Extend time">
            <Btn onClick={() => setPending({ kind: "extend", minutes: 15 })}>+15m</Btn>
            <Btn onClick={() => setPending({ kind: "extend", minutes: 30 })}>+30m</Btn>
            <Btn onClick={() => setPending({ kind: "extend", minutes: 60 })}>+1h</Btn>
          </AdminRow>
          <AdminRow label="Reduce / end">
            <Btn onClick={() => setPending({ kind: "reduce", minutes: 15 })}>-15m</Btn>
            <Btn onClick={() => setPending({ kind: "end-now" })} variant="danger">End now</Btn>
          </AdminRow>
          <AdminRow label="Governance">
            <Btn onClick={() => setPending({ kind: "pause" })} icon={PauseCircle}>Pause</Btn>
            <Btn onClick={() => setPending({ kind: "approve-winner" })} icon={Check} variant="success">
              Approve winner
            </Btn>
            <Btn onClick={() => setPending({ kind: "cancel" })} variant="danger" icon={XCircle}>
              Cancel
            </Btn>
          </AdminRow>
          <AdminRow label="Reserve price">
            <input
              type="number"
              value={reserveInput}
              onChange={(e) => setReserveInput(parseInt(e.target.value || "0", 10))}
              className="w-28 bg-white/5 border border-white/10 text-white text-xs rounded-md px-2 py-1 focus:outline-none focus:ring-1 focus:ring-brand-400"
            />
            <Btn onClick={() => setPending({ kind: "reserve", value: reserveInput })} icon={Settings2}>
              Set reserve
            </Btn>
          </AdminRow>
        </div>
      </article>

      {pending && summary && (
        <DualApprovalModal
          open={!!pending}
          onClose={() => setPending(null)}
          title={summary.title}
          description={summary.desc}
          impact={`Affects lot ${lot.id} · ${lot.quantity} units · ${lot.bidderCount} active bidders`}
          approverLabel="Ops Head approval required (MFA sim)"
          beforeLabel="Before"
          beforeValue={summary.before}
          afterLabel="After"
          afterValue={summary.after}
          auditType={summary.audit}
          actionLabel={summary.label}
          entityLabel={lot.id}
          reasonCode="Admin operational"
        />
      )}
    </>
  );
}

function computeVelocity(lot: AuctionLot): number {
  // Assume bidHistory spans the time from the earliest bid to "now".
  // Most recent bid in mock data is timeAgo strings like "3 min ago", "1 hr ago".
  // Heuristic: convert any entries containing "hr" to 60+ mins; "min" entries use their number.
  const minutesFromTimeAgo = lot.bidHistory
    .map((b) => {
      if (b.timeAgo.includes("hr")) {
        const n = parseFloat(b.timeAgo) || 1;
        return n * 60;
      }
      return parseFloat(b.timeAgo) || 60;
    })
    .reduce((a, b) => Math.max(a, b), 0);
  const minutesElapsed = Math.max(minutesFromTimeAgo, 1);
  return Math.max(1, Math.round((lot.bidHistory.length / minutesElapsed) * 60));
}

function formatExpectedClosing(offsetMinutes: number): string {
  const closing = new Date(Date.now() + offsetMinutes * 60 * 1000);
  try {
    return new Intl.DateTimeFormat("en-IN", {
      timeZone: "Asia/Kolkata",
      hour: "2-digit",
      minute: "2-digit",
      hour12: true,
    }).format(closing);
  } catch {
    return closing.toISOString();
  }
}

function Tile({ label, value, icon: Icon, accent, warn }: { label: string; value: string; icon?: typeof Clock; accent?: boolean; warn?: boolean }) {
  return (
    <div className="rounded-md bg-black/20 border border-white/10 px-2.5 py-2">
      <p className="text-[10px] uppercase tracking-wider text-gray-500 flex items-center gap-1">
        {Icon && <Icon className="h-2.5 w-2.5" />}
        {label}
      </p>
      <p className={cn("text-sm font-bold tabular-nums mt-0.5", accent ? "text-brand-200" : warn ? "text-accent-amber" : "text-white")}>
        {value}
      </p>
    </div>
  );
}

function AdminRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-[10px] uppercase tracking-wider text-gray-500 font-bold w-24 shrink-0">{label}</span>
      <div className="flex items-center gap-1 flex-wrap">{children}</div>
    </div>
  );
}

function Btn({
  onClick,
  children,
  icon: Icon,
  variant = "default",
}: {
  onClick: () => void;
  children: React.ReactNode;
  icon?: typeof Check;
  variant?: "default" | "success" | "danger";
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "inline-flex items-center gap-1 px-2 py-1 text-[11px] font-semibold rounded-md border",
        variant === "danger" && "bg-red-500/10 border-red-500/30 text-red-300 hover:bg-red-500/20",
        variant === "success" && "bg-accent-green/15 border-accent-green/30 text-accent-green hover:bg-accent-green/25",
        variant === "default" && "bg-white/5 border-white/10 text-gray-200 hover:bg-white/10",
      )}
    >
      {Icon && <Icon className="h-3 w-3" />}
      {children}
    </button>
  );
}
