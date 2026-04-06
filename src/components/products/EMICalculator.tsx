"use client";

import { useState } from "react";
import { Calculator, TrendingDown, IndianRupee } from "lucide-react";

export default function EMICalculator() {
  const [price, setPrice] = useState(49000);
  const [rate, setRate] = useState(17.5);
  const [tenure, setTenure] = useState(18);

  const monthlyRate = rate / 100 / 12;
  const n = tenure;
  const emi =
    monthlyRate === 0
      ? price / n
      : (price * monthlyRate * Math.pow(1 + monthlyRate, n)) /
        (Math.pow(1 + monthlyRate, n) - 1);
  const totalPayable = emi * n;
  const totalInterest = totalPayable - price;
  const dailyEMI = emi / 30;

  return (
    <div className="grid gap-8 lg:grid-cols-2">
      {/* Calculator */}
      <div className="rounded-3xl border border-gray-200/60 bg-white shadow-xl shadow-gray-900/5 overflow-hidden">
        <div className="p-6 md:p-8 space-y-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-xl bg-brand-50 flex items-center justify-center">
              <Calculator className="h-5 w-5 text-brand-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 font-sans">EMI Calculator</h3>
          </div>

          {/* Battery Price */}
          <div>
            <div className="flex justify-between text-sm mb-3">
              <label className="font-medium text-gray-600 font-sans">Battery Price</label>
              <span className="font-bold text-brand-700 font-sans">₹{price.toLocaleString("en-IN")}</span>
            </div>
            <input
              type="range"
              min={30000}
              max={80000}
              step={1000}
              value={price}
              onChange={(e) => setPrice(Number(e.target.value))}
              className="w-full accent-brand-600 h-2"
            />
            <div className="flex justify-between text-xs text-gray-400 mt-1.5 font-sans">
              <span>₹30,000</span>
              <span>₹80,000</span>
            </div>
          </div>

          {/* Interest Rate */}
          <div>
            <div className="flex justify-between text-sm mb-3">
              <label className="font-medium text-gray-600 font-sans">Interest Rate</label>
              <span className="font-bold text-brand-700 font-sans">{rate}%</span>
            </div>
            <input
              type="range"
              min={12}
              max={30}
              step={0.5}
              value={rate}
              onChange={(e) => setRate(Number(e.target.value))}
              className="w-full accent-brand-600 h-2"
            />
            <div className="flex justify-between text-xs text-gray-400 mt-1.5 font-sans">
              <span>12%</span>
              <span>30%</span>
            </div>
          </div>

          {/* Tenure */}
          <div>
            <div className="flex justify-between text-sm mb-3">
              <label className="font-medium text-gray-600 font-sans">Tenure</label>
              <span className="font-bold text-brand-700 font-sans">{tenure} months</span>
            </div>
            <input
              type="range"
              min={6}
              max={24}
              step={1}
              value={tenure}
              onChange={(e) => setTenure(Number(e.target.value))}
              className="w-full accent-brand-600 h-2"
            />
            <div className="flex justify-between text-xs text-gray-400 mt-1.5 font-sans">
              <span>6 mo</span>
              <span>24 mo</span>
            </div>
          </div>

          {/* Results */}
          <div className="grid grid-cols-2 gap-3 pt-5 border-t border-gray-100">
            <div className="rounded-2xl bg-gradient-to-br from-brand-50 to-blue-50/50 border border-brand-100/50 p-4 text-center">
              <p className="text-[10px] text-brand-500 font-semibold uppercase tracking-wider mb-1 font-sans">Monthly EMI</p>
              <p className="text-2xl font-bold text-brand-800">₹{Math.round(emi).toLocaleString("en-IN")}</p>
            </div>
            <div className="rounded-2xl bg-gradient-to-br from-emerald-50 to-green-50/50 border border-emerald-100/50 p-4 text-center">
              <p className="text-[10px] text-emerald-600 font-semibold uppercase tracking-wider mb-1 font-sans">Daily EMI</p>
              <p className="text-2xl font-bold text-emerald-700">₹{Math.round(dailyEMI)}</p>
              <p className="text-[10px] text-emerald-500 font-sans">per day</p>
            </div>
            <div className="rounded-2xl bg-surface-warm border border-gray-200/40 p-4 text-center">
              <p className="text-[10px] text-gray-400 font-semibold uppercase tracking-wider mb-1 font-sans">Total Payable</p>
              <p className="text-lg font-bold text-gray-900">₹{Math.round(totalPayable).toLocaleString("en-IN")}</p>
            </div>
            <div className="rounded-2xl bg-surface-warm border border-gray-200/40 p-4 text-center">
              <p className="text-[10px] text-gray-400 font-semibold uppercase tracking-wider mb-1 font-sans">Total Interest</p>
              <p className="text-lg font-bold text-gray-900">₹{Math.round(totalInterest).toLocaleString("en-IN")}</p>
            </div>
          </div>
        </div>
      </div>

      {/* TCO Comparison */}
      <div className="rounded-3xl border border-gray-200/60 bg-white shadow-xl shadow-gray-900/5 overflow-hidden">
        <div className="p-6 md:p-8 space-y-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-xl bg-emerald-50 flex items-center justify-center">
              <TrendingDown className="h-5 w-5 text-emerald-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 font-sans">3-Year TCO Comparison</h3>
          </div>

          {/* iTarang Lithium */}
          <div className="rounded-2xl border-2 border-emerald-200/50 bg-gradient-to-br from-emerald-50/80 to-green-50/30 p-5">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-6 h-6 rounded-lg bg-emerald-500/10 flex items-center justify-center">
                <IndianRupee className="h-3 w-3 text-emerald-700" />
              </div>
              <h4 className="font-semibold text-emerald-800 font-sans text-sm">iTarang Lithium + Financing</h4>
            </div>
            <ul className="space-y-2 text-sm text-emerald-700 font-sans">
              <li>One battery: ₹{price.toLocaleString("en-IN")} with EMI</li>
              <li>Lasts 3-5 years (2,000+ cycles)</li>
              <li>Total cost: ₹{Math.round(totalPayable).toLocaleString("en-IN")}</li>
              <li>Daily cost: ~₹{Math.round(dailyEMI)}/day for {tenure} months only</li>
              <li>Built-in BMS + IoT telemetry</li>
            </ul>
            <div className="mt-4 rounded-xl bg-emerald-500/10 p-3 text-center">
              <span className="text-2xl font-bold text-emerald-800">₹{Math.round(totalPayable).toLocaleString("en-IN")}</span>
              <p className="text-[10px] text-emerald-600 mt-1 font-sans uppercase tracking-wider">Total 3-year cost</p>
            </div>
          </div>

          {/* Lead-Acid */}
          <div className="rounded-2xl border border-gray-200/60 bg-surface-warm p-5">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-6 h-6 rounded-lg bg-gray-200/60 flex items-center justify-center">
                <IndianRupee className="h-3 w-3 text-gray-500" />
              </div>
              <h4 className="font-semibold text-gray-700 font-sans text-sm">Lead-Acid Batteries</h4>
            </div>
            <ul className="space-y-2 text-sm text-gray-600 font-sans">
              <li>₹15,000-18,000 per battery</li>
              <li>Replacement every 8-12 months</li>
              <li>3-4 replacements in 3 years</li>
              <li>No BMS, no data, no warranty after 6 months</li>
              <li>Toxic lead, disposal issues</li>
            </ul>
            <div className="mt-4 rounded-xl bg-gray-200/50 p-3 text-center">
              <span className="text-2xl font-bold text-gray-600">₹45,000 – 72,000</span>
              <p className="text-[10px] text-gray-400 mt-1 font-sans uppercase tracking-wider">Total 3-year cost</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
