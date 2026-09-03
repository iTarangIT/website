"use client";

import { useId, useState, type FormEvent } from "react";
import { Loader2, Search } from "lucide-react";
import { cn } from "@/lib/utils";
import type { NearestResult } from "@/lib/dealers/nearest";

export interface SearchState {
  status: "idle" | "loading" | "done" | "error";
  result: NearestResult | null;
  message: string | null;
}

export const IDLE_SEARCH: SearchState = { status: "idle", result: null, message: null };

interface DealerSearchProps {
  state: SearchState;
  onChange: (state: SearchState) => void;
  className?: string;
}

/**
 * "Find your nearest dealer": one input, one request.
 *
 * Submitted rather than debounced-as-you-type — a half-typed pin code is not a
 * question worth asking the database, and one query per Enter keeps the per-IP
 * ceiling on the endpoint meaningful.
 */
export default function DealerSearch({ state, onChange, className }: DealerSearchProps) {
  const [query, setQuery] = useState("");
  const inputId = useId();
  const busy = state.status === "loading";

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const q = query.trim();
    if (!q || busy) return;

    onChange({ status: "loading", result: null, message: null });
    try {
      const response = await fetch(`/api/dealers/nearest?q=${encodeURIComponent(q)}`);
      const body = await response.json();
      if (!response.ok) {
        onChange({ status: "error", result: null, message: body?.error ?? "Search failed. Please try again." });
        return;
      }
      onChange({ status: "done", result: body as NearestResult, message: null });
    } catch {
      onChange({ status: "error", result: null, message: "Could not reach the dealer search. Please try again." });
    }
  }

  function clear() {
    setQuery("");
    onChange(IDLE_SEARCH);
  }

  return (
    <form role="search" onSubmit={onSubmit} className={cn("mb-6 md:mb-8", className)}>
      <label htmlFor={inputId} className="mb-2 block text-sm font-semibold text-gray-900">
        Find your nearest dealer
      </label>
      <div className="flex flex-col gap-2 sm:flex-row">
        <div className="relative flex-1">
          <Search aria-hidden="true" className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          <input
            id={inputId}
            type="search"
            name="q"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            maxLength={120}
            enterKeyHint="search"
            autoComplete="postal-code"
            placeholder="Pin code, town or address"
            className="w-full rounded-xl border border-gray-200 bg-white py-3 pl-9 pr-3 text-sm text-gray-900 outline-none placeholder:text-gray-400 focus-visible:border-brand-500 focus-visible:ring-2 focus-visible:ring-brand-500/30"
          />
        </div>
        <button
          type="submit"
          disabled={busy || query.trim().length === 0}
          className="inline-flex items-center justify-center gap-2 rounded-xl bg-brand-500 px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-brand-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2 disabled:cursor-default disabled:opacity-50"
        >
          {busy && <Loader2 aria-hidden="true" className="h-4 w-4 animate-spin" />}
          {busy ? "Searching" : "Search"}
        </button>
        {state.status !== "idle" && !busy && (
          <button
            type="button"
            onClick={clear}
            className="rounded-xl px-4 py-3 text-sm font-semibold text-gray-600 transition-colors hover:bg-gray-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
          >
            Clear
          </button>
        )}
      </div>

      <p className="mt-2 text-xs text-gray-500">
        Try a six-digit pin code, or a town such as Lucknow. Distances are straight-line.
      </p>

      {/* The results panel is below the map on a phone, so a visitor who submits
          may see nothing change. Announcing the outcome covers that. */}
      <p aria-live="polite" className="sr-only">
        {state.status === "loading" ? "Searching for dealers" : null}
        {state.status === "error" ? state.message : null}
        {state.status === "done" ? describe(state.result) : null}
      </p>
    </form>
  );
}

function describe(result: NearestResult | null): string {
  if (!result) return "";
  if (!result.resolved) return "We could not place that. Try a pin code or a town name.";
  const n = result.dealers.length;
  if (n === 0) return `No dealers found near ${result.resolved.label}.`;
  const near = result.scope === "state" ? `in ${result.resolved.state}` : `near ${result.resolved.label}`;
  return `${n} dealer${n === 1 ? "" : "s"} found ${near}.`;
}
