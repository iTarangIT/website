"use client";

import { useState } from "react";
import Input from "@/components/ui/Input";
import { Plus, ChevronDown, ChevronUp } from "lucide-react";
import { cn } from "@/lib/utils";
import { cities as cityList } from "@/data/cities";

const LANGUAGES = ["Hindi", "English", "Hinglish", "Bengali", "Tamil", "Telugu", "Marathi"];

export interface NewLeadPayload {
  // Core lead fields
  name: string;
  phone: string;
  shopName: string;
  city: string;
  language: string;
  interest: string;
  // Call context (dynamic variables)
  status: string;
  totalAttempts: string;
  isFollowup: string;
  lastCallMemory: string;
  persistentMemory: string;
  firstMessage: string;
  // Optional hard override of the agent's first_message
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
  const [shopName, setShopName] = useState("");
  const [city, setCity] = useState(cityList[0]?.name ?? "Delhi NCR");
  const [language, setLanguage] = useState("Hindi");
  const [interest, setInterest] = useState("Batteries");

  const [advOpen, setAdvOpen] = useState(false);
  const [status, setStatus] = useState("new");
  const [totalAttempts, setTotalAttempts] = useState("1");
  const [isFollowupBool, setIsFollowupBool] = useState(false);
  const [lastCallMemory, setLastCallMemory] = useState("First call — no prior interaction");
  const [persistentMemory, setPersistentMemory] = useState("");
  const [firstMessage, setFirstMessage] = useState("");
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
      shopName: shopName.trim(),
      city,
      language,
      interest: interest.trim() || "Batteries",
      status: status.trim() || "new",
      totalAttempts: totalAttempts.trim() || "1",
      isFollowup: isFollowupBool ? "1" : "0",
      lastCallMemory: lastCallMemory.trim(),
      persistentMemory: persistentMemory.trim(),
      firstMessage: firstMessage.trim(),
      pitchOverride: pitchOverride.trim() || undefined,
    });

    setName("");
    setPhone("");
    setShopName("");
    setFirstMessage("");
    setPitchOverride("");
    // keep city / language / interest / status / etc. sticky across adds
  };

  return (
    <form onSubmit={submit} className="rounded-xl bg-white/5 border border-white/10 p-4 space-y-3">
      <p className="text-xs font-semibold text-gray-200">Add a lead to dial</p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <Field label="Customer name *">
          <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Apoorv Gupta" className={inputCls} />
        </Field>
        <Field label="Phone *">
          <Input
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            placeholder="+91 78385 97709 or 7838597709"
            className={cn(inputCls, "font-mono")}
          />
        </Field>
        <Field label="Shop name">
          <Input value={shopName} onChange={(e) => setShopName(e.target.value)} placeholder="Lithium Wala" className={inputCls} />
        </Field>
        <Field label="Location / city">
          <select value={city} onChange={(e) => setCity(e.target.value)} className={selectCls}>
            {cityList.map((c) => (
              <option key={c.name} value={c.name} className="bg-gray-950">{c.name}</option>
            ))}
          </select>
        </Field>
        <Field label="Language">
          <select value={language} onChange={(e) => setLanguage(e.target.value)} className={selectCls}>
            {LANGUAGES.map((l) => (
              <option key={l} value={l} className="bg-gray-950">{l}</option>
            ))}
          </select>
        </Field>
        <Field label="Interest">
          <Input value={interest} onChange={(e) => setInterest(e.target.value)} placeholder="Batteries" className={inputCls} />
        </Field>
      </div>

      <button
        type="button"
        onClick={() => setAdvOpen((o) => !o)}
        className="inline-flex items-center gap-1 text-[11px] font-semibold text-gray-400 hover:text-white"
      >
        {advOpen ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
        Call context / advanced variables
        <span className="text-gray-600 font-normal ml-1">
          ({advOpen ? "hide" : "status, memory, first_message…"})
        </span>
      </button>

      {advOpen && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 border-t border-white/5 pt-3">
          <Field label="Status" hint="e.g. new, callback, qualified">
            <Input value={status} onChange={(e) => setStatus(e.target.value)} placeholder="new" className={inputCls} />
          </Field>
          <Field label="Total attempts">
            <Input
              value={totalAttempts}
              onChange={(e) => setTotalAttempts(e.target.value.replace(/\D/g, ""))}
              placeholder="1"
              inputMode="numeric"
              className={cn(inputCls, "font-mono")}
            />
          </Field>
          <Field label="Follow-up call?">
            <label className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/5 border border-white/10 cursor-pointer text-sm text-gray-200">
              <input
                type="checkbox"
                checked={isFollowupBool}
                onChange={(e) => setIsFollowupBool(e.target.checked)}
                className="h-4 w-4 accent-brand-500"
              />
              {isFollowupBool ? "Yes · passes is_followup=1" : "No · passes is_followup=0"}
            </label>
          </Field>

          <div className="md:col-span-3">
            <Field label="Last call memory" hint="Fed into agent as {{last_call_memory}}">
              <textarea
                value={lastCallMemory}
                onChange={(e) => setLastCallMemory(e.target.value)}
                rows={2}
                placeholder="told to call again tomorrow after 5 pm"
                className={textareaCls}
              />
            </Field>
          </div>

          <div className="md:col-span-3">
            <Field label="Persistent memory" hint="Long-lived context across calls — {{persistent_memory}}">
              <textarea
                value={persistentMemory}
                onChange={(e) => setPersistentMemory(e.target.value)}
                rows={2}
                placeholder="Has 14 e-rickshaws running lead-acid. Budget ~₹1.5L."
                className={textareaCls}
              />
            </Field>
          </div>

          <div className="md:col-span-3">
            <Field label="First message" hint="Substitutes {{first_message}} in your agent's opening line">
              <textarea
                value={firstMessage}
                onChange={(e) => setFirstMessage(e.target.value)}
                rows={2}
                placeholder="Namaste Apoorv ji, iTarang AI bol raha hun…"
                className={textareaCls}
              />
            </Field>
          </div>

          <div className="md:col-span-3">
            <Field
              label="Pitch override (hard override)"
              hint="Replaces the agent's entire opening line for this call. Leave blank unless you know you need it."
            >
              <textarea
                value={pitchOverride}
                onChange={(e) => setPitchOverride(e.target.value)}
                rows={2}
                placeholder="Full replacement opener — bypasses your agent's template."
                className={textareaCls}
              />
            </Field>
          </div>
        </div>
      )}

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

const inputCls =
  "bg-white/5 border-white/10 text-white placeholder:text-gray-600";
const selectCls =
  "w-full bg-white/5 border border-white/10 text-white text-sm rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-brand-400";
const textareaCls =
  "w-full text-xs bg-white/5 border border-white/10 text-white rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-brand-400 placeholder:text-gray-600";

function Field({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="block text-[10px] uppercase tracking-wider font-bold text-gray-500 mb-1">{label}</span>
      {children}
      {hint && <p className="text-[10px] text-gray-500 mt-1 leading-tight">{hint}</p>}
    </label>
  );
}
