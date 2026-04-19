"use client";

import { useCallback, useMemo, useState } from "react";

export type SortDir = "asc" | "desc" | "none";

export interface UseTableSortResult<Row, Key extends string> {
  sortKey: Key | null;
  sortDir: SortDir;
  onHeaderClick: (key: Key) => void;
  ariaSortFor: (key: Key) => "ascending" | "descending" | "none";
  sortRows: (rows: Row[]) => Row[];
}

export interface TableSortOptions<Row, Key extends string> {
  initialKey?: Key | null;
  initialDir?: SortDir;
  getValue: (row: Row, key: Key) => string | number | boolean | null | undefined;
}

/**
 * Three-state sort toggle: asc → desc → none → asc → …
 * Cycle on repeated header click; clicking a new header resets to desc (most common expectation for numeric metrics).
 */
export function useTableSort<Row, Key extends string>(
  options: TableSortOptions<Row, Key>,
): UseTableSortResult<Row, Key> {
  const [sortKey, setSortKey] = useState<Key | null>(options.initialKey ?? null);
  const [sortDir, setSortDir] = useState<SortDir>(options.initialDir ?? "desc");

  const onHeaderClick = useCallback(
    (key: Key) => {
      if (sortKey !== key) {
        setSortKey(key);
        setSortDir("desc");
        return;
      }
      // Same column — cycle desc → asc → none
      setSortDir((prev) => (prev === "desc" ? "asc" : prev === "asc" ? "none" : "desc"));
    },
    [sortKey],
  );

  const ariaSortFor = useCallback(
    (key: Key): "ascending" | "descending" | "none" => {
      if (sortKey !== key || sortDir === "none") return "none";
      return sortDir === "asc" ? "ascending" : "descending";
    },
    [sortKey, sortDir],
  );

  const sortRows = useCallback(
    (rows: Row[]): Row[] => {
      if (!sortKey || sortDir === "none") return rows;
      const multiplier = sortDir === "asc" ? 1 : -1;
      return [...rows].sort((a, b) => {
        const av = options.getValue(a, sortKey);
        const bv = options.getValue(b, sortKey);
        if (av == null && bv == null) return 0;
        if (av == null) return 1;
        if (bv == null) return -1;
        if (typeof av === "number" && typeof bv === "number") return (av - bv) * multiplier;
        if (typeof av === "boolean" && typeof bv === "boolean") return (Number(av) - Number(bv)) * multiplier;
        return String(av).localeCompare(String(bv)) * multiplier;
      });
    },
    [sortKey, sortDir, options],
  );

  return useMemo(
    () => ({ sortKey, sortDir, onHeaderClick, ariaSortFor, sortRows }),
    [sortKey, sortDir, onHeaderClick, ariaSortFor, sortRows],
  );
}
