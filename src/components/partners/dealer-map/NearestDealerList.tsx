"use client";

import Link from "next/link";
import { MapPin, Phone } from "lucide-react";
import type { NearestResult, RankedDealer } from "@/lib/dealers/nearest";
import { cn } from "@/lib/utils";

interface NearestDealerListProps {
  result: NearestResult;
  radiusKm: number;
  activeName: string | null;
  onActivate: (name: string | null) => void;
  onClear: () => void;
  className?: string;
}

/**
 * Search results in the side panel, in place of the city list.
 *
 * Mirrors CityList's shell — the same <aside> and scrolling body — so the
 * card's two-column grid does not shift when a search swaps one for the other.
 */
export default function NearestDealerList({
  result,
  radiusKm,
  activeName,
  onActivate,
  onClear,
  className,
}: NearestDealerListProps) {
  const { resolved, dealers, scope, withinRadius } = result;

  return (
    <aside className={cn("flex flex-col", className)} aria-label="Nearest dealers">
      <div className="flex items-start justify-between gap-3 p-5 pb-3 md:p-6 md:pb-4">
        <div className="min-w-0">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-gray-500">
            {scope === "state" ? "Dealers in" : "Nearest to"}
          </p>
          <p className="mt-0.5 truncate text-lg font-bold text-gray-900">
            {resolved ? (scope === "state" ? resolved.state : resolved.label) : "Not found"}
          </p>
          {resolved && scope !== "state" && resolved.state !== resolved.label && (
            <p className="truncate text-xs text-gray-500">{resolved.state}</p>
          )}
        </div>
        <button
          type="button"
          onClick={onClear}
          className="shrink-0 rounded-lg px-2 py-1 text-xs font-semibold text-brand-600 transition-colors hover:bg-brand-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
        >
          All cities
        </button>
      </div>

      <div className="max-h-72 overflow-y-auto px-3 pb-4 lg:max-h-[34rem] lg:px-4 lg:pb-6">
        {!resolved && (
          <Note>
            We could not place that one. Try a six-digit pin code, or a town name such as Lucknow.
          </Note>
        )}

        {resolved && dealers.length === 0 && (
          <Note>
            No active dealers to show yet.{" "}
            <Link href="/contact?role=dealer" className="font-semibold text-brand-600 underline">
              Become a dealer partner
            </Link>
            .
          </Note>
        )}

        {resolved && dealers.length > 0 && !withinRadius && scope === "radius" && (
          <Note>
            No dealer within {radiusKm} km of {resolved.label} yet — here is the closest we have.{" "}
            <Link href="/contact?role=dealer" className="font-semibold text-brand-600 underline">
              Become a dealer partner
            </Link>
            .
          </Note>
        )}

        <ul className="space-y-2">
          {dealers.map((dealer, i) => (
            <li key={`${dealer.company}-${dealer.town}-${i}`}>
              <DealerCard
                dealer={dealer}
                isActive={`${dealer.state}|${dealer.town}` === activeName}
                onActivate={onActivate}
              />
            </li>
          ))}
        </ul>
      </div>
    </aside>
  );
}

function Note({ children }: { children: React.ReactNode }) {
  return <p className="mb-3 rounded-xl bg-amber-50 px-3 py-2.5 text-xs leading-relaxed text-amber-900">{children}</p>;
}

function DealerCard({
  dealer,
  isActive,
  onActivate,
}: {
  dealer: RankedDealer;
  isActive: boolean;
  onActivate: (name: string | null) => void;
}) {
  const key = `${dealer.state}|${dealer.town}`;
  return (
    <div
      onMouseEnter={() => onActivate(key)}
      onMouseLeave={() => onActivate(null)}
      className={cn(
        "rounded-xl border px-3 py-3 transition-colors",
        isActive ? "border-brand-200 bg-brand-50" : "border-gray-100 bg-white hover:bg-gray-50",
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <p className="min-w-0 text-sm font-semibold text-gray-900">{dealer.company}</p>
        {dealer.distanceKm != null && (
          <span className="shrink-0 rounded-full bg-brand-100 px-2 py-0.5 text-[11px] font-semibold tabular-nums text-brand-700">
            {dealer.distanceKm} km
          </span>
        )}
      </div>

      <p className="mt-1 flex items-start gap-1.5 text-xs leading-relaxed text-gray-600">
        <MapPin aria-hidden="true" className="mt-0.5 h-3.5 w-3.5 shrink-0 text-gray-400" />
        <span>
          {dealer.address}
          {/* A state-level address has no honest distance: its coordinates are
              the state's centroid, so we say so instead of printing a number. */}
          {dealer.approximate && (
            <span className="mt-0.5 block text-gray-500">
              In {dealer.state} — exact town not confirmed
            </span>
          )}
        </span>
      </p>

      {dealer.phone ? (
        <a
          href={`tel:${dealer.phone}`}
          className="mt-2 inline-flex items-center gap-1.5 rounded-lg text-xs font-semibold text-brand-600 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
        >
          <Phone aria-hidden="true" className="h-3.5 w-3.5" />
          {dealer.phone}
        </a>
      ) : (
        <Link
          href="/contact?role=dealer"
          className="mt-2 inline-flex items-center gap-1.5 text-xs font-semibold text-brand-600 hover:underline"
        >
          <Phone aria-hidden="true" className="h-3.5 w-3.5" />
          Ask iTarang to connect you
        </Link>
      )}
    </div>
  );
}
