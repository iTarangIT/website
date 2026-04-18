"use client";

import { MapPin, Phone, Battery, Truck, User } from "lucide-react";
import Button from "@/components/ui/Button";
import Badge from "@/components/ui/Badge";
import ScoreBadge from "./ScoreBadge";
import type { Lead, LeadStatus } from "@/lib/nbfc-mock-data";
import { formatCurrency } from "@/lib/utils";

const statusStyles: Record<LeadStatus, string> = {
  New: "bg-gray-100 text-gray-600",
  "AI-Qualified": "bg-green-100 text-green-700",
  "Under Review": "bg-amber-100 text-amber-700",
  Approved: "bg-brand-100 text-brand-700",
};

export default function LeadCard({
  lead,
  onCall,
}: {
  lead: Lead;
  onCall: (lead: Lead) => void;
}) {
  const VehicleIcon = lead.vehicle === "E-Loader" ? Truck : Battery;

  return (
    <article className="flex flex-col rounded-2xl bg-white border border-gray-100 shadow-sm p-5 hover:shadow-md hover:border-gray-200 transition-all">
      <div className="flex items-start gap-3">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-brand-50 text-brand-600">
          <User className="h-5 w-5" />
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="text-sm font-semibold text-gray-900 truncate">{lead.name}</h3>
          <p className="text-xs text-gray-500">
            {lead.age} yrs
            <span className="mx-1.5 text-gray-300">·</span>
            <span className="inline-flex items-center gap-1">
              <MapPin className="h-3 w-3" />
              {lead.city}
            </span>
          </p>
        </div>
        <ScoreBadge value={lead.score} size="sm" />
      </div>

      <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
        <div className="rounded-lg bg-gray-50 border border-gray-100 px-3 py-2">
          <div className="flex items-center gap-1.5 text-gray-500">
            <VehicleIcon className="h-3 w-3" />
            Vehicle
          </div>
          <p className="mt-0.5 font-semibold text-gray-900">{lead.vehicle}</p>
        </div>
        <div className="rounded-lg bg-gray-50 border border-gray-100 px-3 py-2">
          <div className="text-gray-500">Loan requested</div>
          <p className="mt-0.5 font-semibold text-gray-900">{formatCurrency(lead.loanAmount)}</p>
        </div>
      </div>

      <div className="mt-4 flex items-center justify-between">
        <Badge className={statusStyles[lead.status]}>{lead.status}</Badge>
        <span className="text-[10px] text-gray-400">{lead.phoneMasked}</span>
      </div>

      <Button
        onClick={() => onCall(lead)}
        variant="primary"
        size="sm"
        className="mt-4 w-full justify-center gap-2"
      >
        <Phone className="h-4 w-4" />
        Call with AI Dialer
      </Button>
    </article>
  );
}
