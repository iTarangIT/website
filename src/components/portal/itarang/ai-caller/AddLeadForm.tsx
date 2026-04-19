"use client";

import { useState } from "react";
import Input from "@/components/ui/Input";
import { Plus } from "lucide-react";
import { cities as cityList } from "@/data/cities";

const BIZ_TYPES = [
  "E-rickshaw fleet owner",
  "Battery retailer",
  "Charging station operator",
  "Driver union head",
  "E-rickshaw dealer",
  "NBFC / Finance agent",
  "Fleet operator",
  "Battery distributor",
];

export interface NewLeadPayload {
  name: string;
  phone: string;
  businessType: string;
  city: string;
  pitchOverride?: string;
}

interface Props {
  onAdd: (lead: NewLeadPayload) => void;
}

function normalizePhone(raw: string): string {
  const digits = raw.replace(/\D/g, "");
  if (!digits) return "";
  if (digits.startsWith("91") && digits.length >= 12) return `+${digits}`;
  if (digits.length === 10) return `+91${digits}`;
  return `+${digits}`;
}

export default function AddLeadForm({ onAdd }: Props) {
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [businessType, setBusinessType] = useState(BIZ_TYPES[0]);
  const [city, setCity] = useState(cityList[0]?.name ?? "Delhi NCR");
  const [pitchOverride, setPitchOverride] = useState("");
  const [error, setError] = useState<string | null>(null);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!name.trim()) return setError("Name is required");
    const normalized = normalizePhone(phone);
    if (!normalized || normalized.length < 11) return setError("Phone number looks invalid (E.164 or 10-digit Indian)");

    onAdd({
      name: name.trim(),
      phone: normalized,
      businessType,
      city,
      pitchOverride: pitchOverride.trim() || undefined,
    });

    setName("");
    setPhone("");
    setPitchOverride("");
  };

  return (
    <form onSubmit={submit} className="rounded-xl bg-white/5 border border-white/10 p-4 space-y-3">
      <p className="text-xs font-semibold text-gray-200">Add a lead to dial</p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <Field label="Name *">
          <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Anil Sharma" className="bg-white/5 border-white/10 text-white placeholder:text-gray-600" />
        </Field>
        <Field label="Phone *">
          <Input
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            placeholder="+91 98110 12345 or 9811012345"
            className="bg-white/5 border-white/10 text-white placeholder:text-gray-600 font-mono"
          />
        </Field>
        <Field label="Business type">
          <select
            value={businessType}
            onChange={(e) => setBusinessType(e.target.value)}
            className="w-full bg-white/5 border border-white/10 text-white text-sm rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-brand-400"
          >
            {BIZ_TYPES.map((b) => (
              <option key={b} value={b} className="bg-gray-950">{b}</option>
            ))}
          </select>
        </Field>
        <Field label="City">
          <select
            value={city}
            onChange={(e) => setCity(e.target.value)}
            className="w-full bg-white/5 border border-white/10 text-white text-sm rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-brand-400"
          >
            {cityList.map((c) => (
              <option key={c.name} value={c.name} className="bg-gray-950">{c.name}</option>
            ))}
          </select>
        </Field>
      </div>

      <Field label="Pitch override (optional)">
        <textarea
          value={pitchOverride}
          onChange={(e) => setPitchOverride(e.target.value)}
          rows={2}
          placeholder="Replace the agent's default opening message for this call — e.g. reference a prior touchpoint."
          className="w-full text-xs bg-white/5 border border-white/10 text-white rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-brand-400 placeholder:text-gray-600"
        />
      </Field>

      {error && (
        <p role="alert" className="text-xs text-red-300">
          {error}
        </p>
      )}

      <div className="flex justify-end">
        <button
          type="submit"
          className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-md bg-brand-500 text-white hover:bg-brand-600"
        >
          <Plus className="h-3.5 w-3.5" />
          Add lead
        </button>
      </div>
    </form>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="block text-[10px] uppercase tracking-wider font-bold text-gray-500 mb-1">{label}</span>
      {children}
    </label>
  );
}
