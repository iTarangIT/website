"use client";

import { competitors } from "@/data/competitors";
import { cn } from "@/lib/utils";
import Badge from "@/components/ui/Badge";
import { Card, CardContent } from "@/components/ui/Card";
import FadeInOnScroll from "@/components/shared/FadeInOnScroll";
import { CheckCircle, XCircle, Minus } from "lucide-react";

function CellValue({ value }: { value: string }) {
  if (value === "None" || value === "Not Core") {
    return (
      <span className="flex items-center gap-1.5 text-gray-400">
        {value === "None" ? (
          <XCircle className="h-4 w-4 text-red-400" />
        ) : (
          <Minus className="h-4 w-4 text-gray-400" />
        )}
        {value}
      </span>
    );
  }
  return <span>{value}</span>;
}

export default function ComparisonTable() {
  const columns = [
    { key: "assetFocus", label: "Asset Focus" },
    { key: "iotRiskTech", label: "IoT & Risk Tech" },
    { key: "lifecycleEPR", label: "Lifecycle / EPR" },
    { key: "businessModel", label: "Business Model" },
    { key: "validation", label: "Validation" },
  ] as const;

  return (
    <>
      {/* Desktop Table */}
      <FadeInOnScroll className="hidden lg:block">
        <div className="overflow-x-auto rounded-2xl border border-gray-200 bg-white shadow-sm">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className="px-6 py-4 text-left font-semibold text-gray-900">
                  Company
                </th>
                {columns.map((col) => (
                  <th
                    key={col.key}
                    className="px-6 py-4 text-left font-semibold text-gray-900"
                  >
                    {col.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {competitors.map((competitor, idx) => (
                <tr
                  key={competitor.name}
                  className={cn(
                    "border-b border-gray-100 transition-colors",
                    competitor.highlight
                      ? "bg-brand-50 border-l-4 border-l-brand-500"
                      : idx % 2 === 0
                        ? "bg-white"
                        : "bg-gray-50/50"
                  )}
                >
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <span
                        className={cn(
                          "font-semibold",
                          competitor.highlight
                            ? "text-brand-700"
                            : "text-gray-900"
                        )}
                      >
                        {competitor.name}
                      </span>
                      {competitor.highlight && (
                        <CheckCircle className="h-4 w-4 text-brand-500" />
                      )}
                    </div>
                  </td>
                  {columns.map((col) => (
                    <td
                      key={col.key}
                      className={cn(
                        "px-6 py-4",
                        competitor.highlight
                          ? "text-gray-800 font-medium"
                          : "text-gray-600"
                      )}
                    >
                      {competitor[col.key] ? (
                        <CellValue value={competitor[col.key] as string} />
                      ) : (
                        <span className="text-gray-300">&mdash;</span>
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </FadeInOnScroll>

      {/* Mobile Card View */}
      <div className="lg:hidden space-y-4">
        {competitors.map((competitor, idx) => (
          <FadeInOnScroll key={competitor.name} delay={idx * 0.08}>
            <Card
              className={cn(
                competitor.highlight &&
                  "border-brand-200 bg-brand-50 ring-1 ring-brand-200"
              )}
            >
              <CardContent>
                <div className="flex items-center justify-between mb-4">
                  <h3
                    className={cn(
                      "text-lg font-bold",
                      competitor.highlight ? "text-brand-700" : "text-gray-900"
                    )}
                  >
                    {competitor.name}
                  </h3>
                  {competitor.highlight && (
                    <Badge>Full Lifecycle TSP</Badge>
                  )}
                </div>
                <dl className="space-y-3">
                  {columns.map((col) => (
                    <div key={col.key}>
                      <dt className="text-xs font-semibold uppercase tracking-wider text-gray-500">
                        {col.label}
                      </dt>
                      <dd className="mt-0.5 text-sm text-gray-800">
                        {competitor[col.key] ? (
                          <CellValue value={competitor[col.key] as string} />
                        ) : (
                          <span className="text-gray-300">&mdash;</span>
                        )}
                      </dd>
                    </div>
                  ))}
                </dl>
              </CardContent>
            </Card>
          </FadeInOnScroll>
        ))}
      </div>
    </>
  );
}
