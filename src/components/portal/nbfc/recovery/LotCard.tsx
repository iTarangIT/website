"use client";

import { Users, Clock, Tag } from "lucide-react";
import { cn } from "@/lib/utils";
import { useCountdown } from "@/lib/auction-clock";
import type { AuctionLot } from "@/data/portal/auction";

interface Props {
  lot: AuctionLot;
  onEnter: () => void;
}

const STATUS_CLS = {
  live: "text-accent-green",
  "closing-soon": "text-accent-amber animate-pulse",
  upcoming: "text-gray-400",
  settled: "text-gray-500",
  "no-bids": "text-gray-500",
};

export default function LotCard({ lot, onEnter }: Props) {
  const { formatted, expired } = useCountdown(lot.endsAtIsoOffsetMinutes, lot.status === "settled");

  return (
    <article className="rounded-xl bg-white/5 border border-white/10 p-4 flex flex-col gap-3 hover:border-white/20 transition-colors">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-xs font-mono text-gray-500">{lot.id}</p>
          <p className="text-sm font-bold text-white">{lot.capacity}</p>
          <p className="text-[11px] text-gray-400">{lot.modelMix}</p>
        </div>
        <span className={cn("inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider", STATUS_CLS[lot.status])}>
          <span className="h-1.5 w-1.5 rounded-full bg-current" />
          {lot.status.replace("-", " ")}
        </span>
      </div>

      <div className="aspect-[5/3] rounded-lg bg-gradient-to-br from-brand-500/15 to-brand-700/5 border border-white/5 flex items-center justify-center">
        <p className="text-[10px] text-gray-500 italic">Lot image</p>
      </div>

      <dl className="grid grid-cols-2 gap-1.5 text-[11px]">
        <dt className="text-gray-500">SOH range</dt>
        <dd className="text-gray-200 text-right">{lot.avgSohRange}</dd>
        <dt className="text-gray-500">Age</dt>
        <dd className="text-gray-200 text-right">{lot.age}</dd>
        <dt className="text-gray-500">Quantity</dt>
        <dd className="text-gray-200 text-right">{lot.quantity} units</dd>
        <dt className="text-gray-500">Charger</dt>
        <dd className="text-gray-200 text-right">{lot.chargerType}</dd>
      </dl>

      <div className="rounded-lg bg-black/30 border border-white/10 px-3 py-2 space-y-1">
        <div className="flex items-center justify-between text-[10px] text-gray-500">
          <span className="flex items-center gap-1">
            <Tag className="h-2.5 w-2.5" />
            Base
          </span>
          <span className="flex items-center gap-1">
            <Users className="h-2.5 w-2.5" />
            {lot.bidderCount} bidders
          </span>
        </div>
        <div className="flex items-baseline justify-between">
          <span className="text-xs text-gray-400 tabular-nums">₹{lot.basePrice.toLocaleString("en-IN")}</span>
          <span className={cn("text-sm font-bold tabular-nums", lot.currentBid > lot.basePrice ? "text-accent-green" : "text-gray-300")}>
            ₹{lot.currentBid.toLocaleString("en-IN")}
          </span>
        </div>
      </div>

      <div className="flex items-center justify-between text-[11px]">
        <span className={cn("inline-flex items-center gap-1 font-mono tabular-nums", expired ? "text-red-400" : "text-accent-amber")}>
          <Clock className="h-3 w-3" />
          {expired ? "Ended" : formatted}
        </span>
        <button
          onClick={onEnter}
          className="px-3 py-1.5 text-[11px] font-semibold rounded-md bg-brand-500 text-white hover:bg-brand-600"
        >
          Enter lot
        </button>
      </div>
    </article>
  );
}
