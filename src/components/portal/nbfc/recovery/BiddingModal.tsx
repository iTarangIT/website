"use client";

import { useMemo, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Clock, Gavel, LogOut, TrendingUp } from "lucide-react";
import { cn } from "@/lib/utils";
import { useCountdown } from "@/lib/auction-clock";
import type { AuctionLot } from "@/data/portal/auction";
import { appendAuditEntry } from "@/lib/audit-store";

interface Props {
  lot: AuctionLot | null;
  onClose: () => void;
}

export default function BiddingModal({ lot, onClose }: Props) {
  const [currentBid, setCurrentBid] = useState<number>(lot?.currentBid ?? 0);
  const [nextBid, setNextBid] = useState<number>((lot?.currentBid ?? 0) + 2000);
  const [history, setHistory] = useState(lot?.bidHistory ?? []);
  const [outbid, setOutbid] = useState(false);
  const [confirm, setConfirm] = useState<{ amount: number } | null>(null);

  const { formatted, expired } = useCountdown(lot?.endsAtIsoOffsetMinutes ?? 60);

  const minBid = useMemo(() => currentBid + 2000, [currentBid]);

  if (!lot) return null;

  const place = () => {
    if (nextBid < minBid) return;
    setConfirm({ amount: nextBid });
  };

  const commit = () => {
    if (!confirm) return;
    const amount = confirm.amount;
    setHistory((h) => [{ bidder: "You (Bidder #B-2401)", amount, timeAgo: "just now" }, ...h]);
    setCurrentBid(amount);
    setNextBid(amount + 2000);
    setOutbid(false);
    appendAuditEntry({
      actionType: "bid-placed",
      actionLabel: "Bid placed",
      entity: lot.id,
      reasonCode: "Dealer bid",
      requestedBy: "You (Bidder #B-2401)",
      approvedBy: null,
      status: "completed",
      afterValue: `₹${amount.toLocaleString("en-IN")}`,
    });
    setConfirm(null);
    setTimeout(() => setOutbid(true), 4500);
  };

  return (
    <>
      <Dialog open={!!lot} onOpenChange={(o) => !o && onClose()}>
        <DialogContent className="sm:max-w-[560px] bg-gray-950 text-white border border-white/10">
          <DialogHeader>
            <DialogTitle className="text-white">Lot {lot.id} · {lot.capacity}</DialogTitle>
            <DialogDescription className="text-gray-400 text-xs">
              {lot.quantity} units · {lot.modelMix} · {lot.age}
            </DialogDescription>
          </DialogHeader>

          <section className="space-y-4 pt-1">
            <div className="grid grid-cols-3 gap-3 text-xs">
              <Tile
                label="Current highest bid"
                value={`₹${currentBid.toLocaleString("en-IN")}`}
                accent
              />
              <Tile
                label="Your status"
                value={outbid ? "OUTBID" : history.some((h) => h.bidder.startsWith("You")) ? "Leading" : "—"}
                status={outbid ? "danger" : history.some((h) => h.bidder.startsWith("You")) ? "good" : "default"}
              />
              <Tile label="Time remaining" value={expired ? "Ended" : formatted} icon={Clock} status={expired ? "danger" : "warning"} />
            </div>

            <div className="rounded-lg bg-black/30 border border-white/10 px-4 py-3 space-y-3">
              <label className="block text-[11px] uppercase tracking-wider font-bold text-gray-500">
                Your bid (min ₹{minBid.toLocaleString("en-IN")})
              </label>
              <input
                type="number"
                min={minBid}
                step={1000}
                value={nextBid}
                onChange={(e) => setNextBid(parseInt(e.target.value || "0", 10))}
                className="w-full bg-white/5 border border-white/10 text-white text-xl font-bold tabular-nums rounded-md px-3 py-2 focus:outline-none focus:ring-1 focus:ring-brand-400"
              />
              <div className="flex items-center gap-2">
                <button
                  onClick={place}
                  disabled={expired || nextBid < minBid}
                  className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-md bg-brand-500 text-white hover:bg-brand-600 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <Gavel className="h-3.5 w-3.5" />
                  Place bid
                </button>
                <button
                  onClick={() => setNextBid(minBid + 8000)}
                  className="px-3 py-2 text-xs font-medium rounded-md bg-white/5 border border-white/10 text-gray-300 hover:bg-white/10"
                >
                  Auto-bid max
                </button>
                <button
                  onClick={onClose}
                  className="inline-flex items-center gap-1 px-3 py-2 text-xs font-medium rounded-md text-gray-400 hover:bg-white/5"
                >
                  <LogOut className="h-3 w-3" />
                  Exit
                </button>
              </div>
            </div>

            <div className="rounded-lg bg-black/30 border border-white/10">
              <div className="flex items-center justify-between px-4 py-2 border-b border-white/10">
                <p className="text-[11px] font-semibold text-gray-300 flex items-center gap-1">
                  <TrendingUp className="h-3 w-3" />
                  Bid history
                </p>
                <span className="text-[10px] text-gray-500">{history.length} bids</span>
              </div>
              <ul className="max-h-48 overflow-y-auto divide-y divide-white/5">
                {history.map((h, i) => (
                  <li key={i} className="flex items-center justify-between gap-3 px-4 py-2 text-xs">
                    <span className={cn("text-gray-300 truncate", i === 0 && "text-white font-semibold")}>
                      {h.bidder}
                    </span>
                    <span className="text-white tabular-nums">₹{h.amount.toLocaleString("en-IN")}</span>
                    <span className="text-gray-500 text-[10px] shrink-0">{h.timeAgo}</span>
                  </li>
                ))}
              </ul>
            </div>

            <p className="text-[10px] text-gray-500">Every bid is binding. Audit entry logged on confirmation.</p>
          </section>
        </DialogContent>
      </Dialog>

      {/* Confirm modal */}
      <Dialog open={!!confirm} onOpenChange={(o) => !o && setConfirm(null)}>
        <DialogContent className="sm:max-w-[400px] bg-gray-950 text-white border border-white/10">
          <DialogHeader>
            <DialogTitle className="text-white">Confirm bid</DialogTitle>
          </DialogHeader>
          <p className="text-sm text-gray-300">
            Confirm bid of <span className="font-bold text-white">₹{confirm?.amount.toLocaleString("en-IN")}</span>? This is binding.
          </p>
          <div className="flex items-center justify-end gap-2 pt-2">
            <button onClick={() => setConfirm(null)} className="px-3 py-2 text-xs font-medium rounded-md text-gray-300 hover:bg-white/5">Cancel</button>
            <button onClick={commit} className="px-3 py-2 text-xs font-semibold rounded-md bg-accent-green text-white hover:bg-accent-green/90">Confirm</button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}

function Tile({
  label,
  value,
  icon: Icon,
  accent,
  status = "default",
}: {
  label: string;
  value: string;
  icon?: typeof Clock;
  accent?: boolean;
  status?: "default" | "good" | "warning" | "danger";
}) {
  const cls = accent
    ? "text-brand-200"
    : status === "good"
    ? "text-accent-green"
    : status === "warning"
    ? "text-accent-amber"
    : status === "danger"
    ? "text-red-400"
    : "text-white";
  return (
    <div className="rounded-lg bg-black/20 border border-white/10 p-3">
      <p className="text-[10px] uppercase tracking-wider text-gray-500 mb-1 flex items-center gap-1">
        {Icon && <Icon className="h-2.5 w-2.5" />}
        {label}
      </p>
      <p className={cn("text-lg font-bold tabular-nums", cls)}>{value}</p>
    </div>
  );
}
