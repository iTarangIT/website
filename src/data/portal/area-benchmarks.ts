export interface AreaBenchmark {
  city: string;
  avgDailyKm: { median: number; topQuartile: number };
  sohPct: { median: number; topQuartile: number };
  dpd: { median: number; topQuartile: number };
  cdsScore: { median: number; topQuartile: number };
}

export const areaBenchmarks: AreaBenchmark[] = [
  {
    city: "Delhi NCR",
    avgDailyKm: { median: 48, topQuartile: 56 },
    sohPct: { median: 96.5, topQuartile: 98.2 },
    dpd: { median: 2, topQuartile: 0 },
    cdsScore: { median: 12, topQuartile: 4 },
  },
  {
    city: "Lucknow",
    avgDailyKm: { median: 44, topQuartile: 52 },
    sohPct: { median: 95.2, topQuartile: 97.8 },
    dpd: { median: 4, topQuartile: 0 },
    cdsScore: { median: 18, topQuartile: 6 },
  },
  {
    city: "Kolkata",
    avgDailyKm: { median: 46, topQuartile: 54 },
    sohPct: { median: 95.8, topQuartile: 97.5 },
    dpd: { median: 3, topQuartile: 0 },
    cdsScore: { median: 14, topQuartile: 5 },
  },
  {
    city: "Patna",
    avgDailyKm: { median: 42, topQuartile: 50 },
    sohPct: { median: 94.8, topQuartile: 97.2 },
    dpd: { median: 5, topQuartile: 0 },
    cdsScore: { median: 20, topQuartile: 8 },
  },
  {
    city: "Varanasi",
    avgDailyKm: { median: 40, topQuartile: 48 },
    sohPct: { median: 94.2, topQuartile: 96.8 },
    dpd: { median: 6, topQuartile: 0 },
    cdsScore: { median: 22, topQuartile: 10 },
  },
];

export function getBenchmark(city: string): AreaBenchmark | undefined {
  return areaBenchmarks.find((b) => b.city === city);
}
