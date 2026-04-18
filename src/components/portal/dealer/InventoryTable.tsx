"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { dealerInventory, type InventoryItem } from "@/data/portal/dealer-mock";

const STATUS_STYLES: Record<InventoryItem["status"], string> = {
  Deployed: "bg-accent-green/20 text-accent-green",
  "In Stock": "bg-brand-500/20 text-brand-300",
  "In Service": "bg-accent-amber/20 text-accent-amber",
  "In Transit": "bg-white/10 text-gray-300",
};

export default function InventoryTable() {
  const [toast, setToast] = useState<string | null>(null);
  const fire = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 2000);
  };

  return (
    <section className="rounded-xl bg-white/5 border border-white/10 overflow-hidden">
      <div className="flex items-center justify-between px-5 py-4 border-b border-white/10">
        <div>
          <h4 className="text-sm font-semibold text-gray-200">Inventory</h4>
          <p className="text-xs text-gray-500 mt-0.5">Latest 6 batteries</p>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead className="bg-black/20">
            <tr className="text-left text-gray-500">
              <th className="px-5 py-2.5 font-medium">Serial</th>
              <th className="px-3 py-2.5 font-medium">Model</th>
              <th className="px-3 py-2.5 font-medium">Status</th>
              <th className="px-3 py-2.5 font-medium">Health</th>
              <th className="px-3 py-2.5 font-medium">Consumer</th>
              <th className="px-5 py-2.5 font-medium text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {dealerInventory.map((it) => (
              <tr key={it.serial} className="hover:bg-white/5">
                <td className="px-5 py-2.5 font-mono text-gray-200">{it.serial}</td>
                <td className="px-3 py-2.5 text-gray-300">{it.model}</td>
                <td className="px-3 py-2.5">
                  <span className={cn("inline-flex px-2 py-0.5 rounded-full text-[10px] font-semibold", STATUS_STYLES[it.status])}>
                    {it.status}
                  </span>
                </td>
                <td className="px-3 py-2.5 font-semibold tabular-nums text-gray-200">{it.health}%</td>
                <td className="px-3 py-2.5 text-gray-300">{it.consumer ?? "—"}</td>
                <td className="px-5 py-2.5 text-right">
                  <button
                    onClick={() =>
                      fire(it.status === "In Stock" ? `Deployment started for ${it.serial}` : `Opening ${it.serial}`)
                    }
                    className="text-[11px] font-medium px-2.5 py-1 rounded-md bg-white/5 text-gray-300 hover:bg-white/10"
                  >
                    {it.status === "In Stock" ? "Deploy" : "View"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {toast && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 bg-gray-900 border border-white/10 text-white text-xs px-3.5 py-2 rounded-lg shadow-xl z-50">
          {toast}
        </div>
      )}
    </section>
  );
}
