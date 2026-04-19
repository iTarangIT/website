"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Settings2, CheckCircle2, XCircle, Loader2 } from "lucide-react";
import Input from "@/components/ui/Input";
import {
  readElevenLabsSettings,
  writeElevenLabsSettings,
  testAgent,
  type ElevenLabsSettings,
} from "@/lib/elevenlabs";

interface Props {
  onClose: () => void;
  open: boolean;
}

export default function AICallerSettings({ open, onClose }: Props) {
  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="sm:max-w-[540px] bg-gray-950 text-white border border-white/10">
        <DialogHeader>
          <DialogTitle className="text-white flex items-center gap-2">
            <Settings2 className="h-4 w-4 text-brand-300" />
            ElevenLabs agent settings
          </DialogTitle>
          <DialogDescription className="text-gray-400 text-xs">
            API key is stored on the server (ELEVENLABS_API_KEY). Agent &amp; phone number ids are saved in your browser.
          </DialogDescription>
        </DialogHeader>

        {open && <SettingsForm onClose={onClose} />}
      </DialogContent>
    </Dialog>
  );
}

function SettingsForm({ onClose }: { onClose: () => void }) {
  const initial: ElevenLabsSettings =
    typeof window === "undefined"
      ? { agentId: "", phoneNumberId: "", fromName: "iTarang AI", provider: "sip-trunk" }
      : readElevenLabsSettings();

  const [agentId, setAgentId] = useState(initial.agentId);
  const [phoneNumberId, setPhoneNumberId] = useState(initial.phoneNumberId);
  const [fromName, setFromName] = useState(initial.fromName || "iTarang AI");
  const [provider, setProvider] = useState<"sip-trunk" | "twilio">(initial.provider);
  const [testState, setTestState] = useState<"idle" | "testing" | "ok" | "fail">("idle");
  const [testMessage, setTestMessage] = useState<string | null>(null);

  const save = () => {
    writeElevenLabsSettings({
      agentId: agentId.trim(),
      phoneNumberId: phoneNumberId.trim(),
      fromName: fromName.trim(),
      provider,
    });
    onClose();
  };

  const test = async () => {
    if (!agentId.trim()) {
      setTestState("fail");
      setTestMessage("Enter an agent ID first");
      return;
    }
    setTestState("testing");
    setTestMessage(null);
    const result = await testAgent(agentId.trim());
    if (result.ok) {
      setTestState("ok");
      setTestMessage(`Connected — ${result.agentName}`);
    } else {
      setTestState("fail");
      setTestMessage(result.error || "Agent lookup failed");
    }
  };

  return (
    <div className="space-y-4 pt-2">
      <Field label="Agent ID" required>
        <Input
          value={agentId}
          onChange={(e) => setAgentId(e.target.value)}
          placeholder="agent_xxxxxxxxxxxxxxxxxxxxxxx"
          className="bg-white/5 border-white/10 text-white placeholder:text-gray-600 font-mono text-xs"
        />
      </Field>

      <Field label="Agent phone-number ID" required>
        <Input
          value={phoneNumberId}
          onChange={(e) => setPhoneNumberId(e.target.value)}
          placeholder="pn_xxxxxxxxxxxxxxxxxxxxxxx"
          className="bg-white/5 border-white/10 text-white placeholder:text-gray-600 font-mono text-xs"
        />
        <p className="mt-1 text-[10px] text-gray-500">
          Found under <span className="font-mono">Phone Numbers</span> in the ElevenLabs Agents dashboard.
        </p>
      </Field>

      <Field label="Provider">
        <select
          value={provider}
          onChange={(e) => setProvider(e.target.value as "sip-trunk" | "twilio")}
          className="w-full bg-white/5 border border-white/10 text-white text-sm rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-brand-400"
        >
          <option value="sip-trunk" className="bg-gray-950">SIP trunk (recommended — Vobiz)</option>
          <option value="twilio" className="bg-gray-950">Twilio</option>
        </select>
      </Field>

      <Field label="From name (display only)">
        <Input
          value={fromName}
          onChange={(e) => setFromName(e.target.value)}
          placeholder="iTarang AI"
          className="bg-white/5 border-white/10 text-white placeholder:text-gray-600"
        />
      </Field>

      <div className="rounded-lg bg-black/30 border border-white/10 p-3 text-[11px] text-gray-400 flex items-center justify-between gap-3">
        <div className="min-w-0 flex items-center gap-2">
          {testState === "testing" && <Loader2 className="h-3.5 w-3.5 animate-spin text-brand-200 shrink-0" />}
          {testState === "ok" && <CheckCircle2 className="h-3.5 w-3.5 text-accent-green shrink-0" />}
          {testState === "fail" && <XCircle className="h-3.5 w-3.5 text-red-300 shrink-0" />}
          <span className="truncate">
            {testMessage ?? "Use Test to verify the agent ID against your ElevenLabs account."}
          </span>
        </div>
        <button
          onClick={test}
          disabled={testState === "testing"}
          className="shrink-0 px-2.5 py-1 text-[11px] font-semibold rounded-md bg-white/5 border border-white/10 text-gray-200 hover:bg-white/10 disabled:opacity-50"
        >
          Test
        </button>
      </div>

      <div className="flex items-center justify-end gap-2 pt-1">
        <button onClick={onClose} className="px-3 py-2 text-xs font-medium rounded-md text-gray-300 hover:bg-white/5">
          Cancel
        </button>
        <button
          onClick={save}
          disabled={!agentId.trim() || !phoneNumberId.trim()}
          className="px-3 py-2 text-xs font-semibold rounded-md bg-brand-500 text-white hover:bg-brand-600 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          Save
        </button>
      </div>
    </div>
  );
}

function Field({ label, required, children }: { label: string; required?: boolean; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="block text-[10px] uppercase tracking-wider font-bold text-gray-500 mb-1">
        {label}
        {required && <span className="text-red-400 ml-0.5">*</span>}
      </span>
      {children}
    </label>
  );
}
