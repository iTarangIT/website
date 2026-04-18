"use client";

import { useState } from "react";
import { Settings, X, Save, Trash2, TestTube } from "lucide-react";
import { cn } from "@/lib/utils";
import Input from "@/components/ui/Input";

const WEBHOOK_KEY = "itarang:n8n-webhook";

export default function WebhookSettings({ inline = false }: { inline?: boolean }) {
  const [open, setOpen] = useState(false);
  const [url, setUrl] = useState<string>(() =>
    typeof window === "undefined" ? "" : window.localStorage.getItem(WEBHOOK_KEY) ?? "",
  );
  const [saved, setSaved] = useState<string | null>(() =>
    typeof window === "undefined" ? null : window.localStorage.getItem(WEBHOOK_KEY),
  );
  const [testResult, setTestResult] = useState<string | null>(null);

  const openWithLatest = () => {
    if (typeof window !== "undefined") {
      const stored = window.localStorage.getItem(WEBHOOK_KEY) ?? "";
      setUrl(stored);
      setSaved(stored || null);
    }
    setOpen(true);
  };

  const save = () => {
    const trimmed = url.trim();
    if (!trimmed) {
      window.localStorage.removeItem(WEBHOOK_KEY);
      setSaved(null);
    } else {
      window.localStorage.setItem(WEBHOOK_KEY, trimmed);
      setSaved(trimmed);
    }
    setTestResult("Saved");
    setTimeout(() => setTestResult(null), 1500);
  };

  const clear = () => {
    window.localStorage.removeItem(WEBHOOK_KEY);
    setUrl("");
    setSaved(null);
    setTestResult("Cleared");
    setTimeout(() => setTestResult(null), 1500);
  };

  const test = async () => {
    if (!url.trim()) {
      setTestResult("Enter URL first");
      return;
    }
    setTestResult("Testing…");
    try {
      const controller = new AbortController();
      const t = setTimeout(() => controller.abort(), 5000);
      const res = await fetch(url.trim(), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ test: true, source: "itarang-portal" }),
        signal: controller.signal,
        mode: "cors",
      });
      clearTimeout(t);
      setTestResult(`HTTP ${res.status}`);
    } catch (e) {
      setTestResult(e instanceof Error && e.name === "AbortError" ? "Timeout" : "Request failed (CORS or network)");
    }
  };

  return (
    <>
      <button
        onClick={openWithLatest}
        className={cn(
          "inline-flex items-center gap-1.5 text-xs font-medium rounded-md transition-colors",
          inline
            ? "px-3 py-1.5 bg-brand-500/10 border border-brand-500/30 text-brand-200 hover:bg-brand-500/20"
            : "px-2 py-1.5 text-gray-400 hover:text-white hover:bg-white/5",
        )}
        title="AI dialer webhook settings"
      >
        <Settings className="h-3.5 w-3.5" />
        <span className={cn(!inline && "hidden sm:inline")}>Dialer settings</span>
        {saved && <span className="h-1.5 w-1.5 rounded-full bg-accent-green" />}
      </button>

      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80" onClick={() => setOpen(false)}>
          <div
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-md rounded-2xl bg-gray-950 border border-white/10 shadow-2xl overflow-hidden"
          >
            <div className="flex items-center justify-between px-5 py-4 border-b border-white/10">
              <div>
                <h3 className="text-base font-semibold text-white">AI dialer webhook</h3>
                <p className="text-[11px] text-gray-500 mt-0.5">Triggers n8n → ElevenLabs outbound calls</p>
              </div>
              <button onClick={() => setOpen(false)} className="p-1.5 rounded-md text-gray-400 hover:text-white hover:bg-white/5">
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="px-5 py-5 space-y-4">
              <div>
                <label className="block text-xs font-medium text-gray-300 mb-1.5">n8n webhook URL</label>
                <Input
                  type="url"
                  placeholder="https://your-n8n.example.com/webhook/ai-dialer"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  className="bg-white/5 border-white/10 text-white placeholder:text-gray-600"
                />
                <p className="text-[11px] text-gray-500 mt-1.5 leading-relaxed">
                  POST body: <span className="font-mono text-gray-400">{"{ leadId, phone, name, businessName, leadType, city, area, source, script }"}</span>.
                  Leave empty to run the AI dialer in offline demo mode.
                </p>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={save}
                  className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-lg bg-brand-500 text-white hover:bg-brand-600"
                >
                  <Save className="h-3.5 w-3.5" />
                  Save
                </button>
                <button
                  onClick={test}
                  className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-lg bg-white/5 border border-white/10 text-gray-200 hover:bg-white/10"
                >
                  <TestTube className="h-3.5 w-3.5" />
                  Test call
                </button>
                <button
                  onClick={clear}
                  className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-medium rounded-lg text-red-400 hover:bg-red-500/10"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                  Clear
                </button>
                {testResult && (
                  <span className="ml-auto text-[11px] text-gray-400">{testResult}</span>
                )}
              </div>

              <div className="rounded-lg bg-black/30 border border-white/5 px-3 py-2 text-[11px] text-gray-400 leading-relaxed">
                Current status:{" "}
                {saved ? (
                  <span className="text-accent-green font-semibold">Webhook configured</span>
                ) : (
                  <span className="text-gray-500">Offline demo mode</span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
