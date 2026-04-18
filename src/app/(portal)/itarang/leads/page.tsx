import { Sparkles, Info } from "lucide-react";
import LeadsPipeline from "@/components/portal/itarang/LeadsPipeline";
import WebhookSettings from "@/components/portal/itarang/WebhookSettings";

export default function LeadsPage() {
  return (
    <div className="px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-white tracking-tight flex items-center gap-2">
            Leads
            <Sparkles className="h-5 w-5 text-accent-amber" />
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            AI-powered pipeline: scrape → qualify → hand off. All the heavy lifting on autopilot.
          </p>
        </div>
        <WebhookSettings inline />
      </div>

      {/* Explainer banner */}
      <div className="rounded-xl bg-gradient-to-r from-brand-500/15 via-brand-500/5 to-transparent border border-brand-500/20 px-5 py-4">
        <div className="flex items-start gap-3">
          <div className="h-8 w-8 rounded-lg bg-brand-500/20 border border-brand-500/30 flex items-center justify-center shrink-0">
            <Info className="h-4 w-4 text-brand-300" />
          </div>
          <div className="text-xs text-gray-300 leading-relaxed">
            <p className="font-semibold text-white mb-1">How the pipeline works</p>
            <p>
              Leads are scraped from <span className="font-semibold text-purple-300">Apify</span> (business directories),{" "}
              <span className="font-semibold text-emerald-300">Google Maps</span> (location search) and{" "}
              <span className="font-semibold text-orange-300">Firecrawl</span> (website extraction). The AI dialer places outbound
              calls via <span className="font-semibold text-accent-amber">n8n → ElevenLabs</span>, qualifies intent, and scores each lead 0–100 on{" "}
              <span className="text-white">Capability</span>,{" "}
              <span className="text-white">Response</span>,{" "}
              <span className="text-white">Timing</span>,{" "}
              <span className="text-white">Budget</span> &{" "}
              <span className="text-white">Readiness</span>. Leads scoring ≥ 60 are handed to the sales team.
            </p>
          </div>
        </div>
      </div>

      <LeadsPipeline />
    </div>
  );
}
