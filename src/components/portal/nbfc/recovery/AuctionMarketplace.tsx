"use client";

import { useState } from "react";
import { auctionLots, type AuctionLot } from "@/data/portal/auction";
import LotCard from "./LotCard";
import BiddingModal from "./BiddingModal";

export default function AuctionMarketplace() {
  const [active, setActive] = useState<AuctionLot | null>(null);

  return (
    <>
      <section>
        <div className="flex items-center justify-between gap-3 mb-4 flex-wrap">
          <div>
            <h4 className="text-sm font-semibold text-gray-200">Auction marketplace</h4>
            <p className="text-[11px] text-gray-500 mt-0.5">{auctionLots.length} lots live · timers update every second</p>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
          {auctionLots.map((lot) => (
            <LotCard key={lot.id} lot={lot} onEnter={() => setActive(lot)} />
          ))}
        </div>
      </section>

      <BiddingModal lot={active} onClose={() => setActive(null)} />
    </>
  );
}
