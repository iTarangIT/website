/* Google Analytics 4 — the browser half.
 *
 * The tag is mounted once in the root layout and is a no-op unless
 * NEXT_PUBLIC_GA4_MEASUREMENT_ID is set, so a local checkout and a preview
 * deploy stay out of the production property.
 *
 * The dashboard reads this data back through the GA4 Data API
 * (cmo-dashboard/analytics_readers.py). Event and parameter names here are the
 * contract with that reader — renaming one silently empties a console panel.
 */

export const GA_MEASUREMENT_ID = process.env.NEXT_PUBLIC_GA4_MEASUREMENT_ID ?? "";

/**
 * Whether the *direct* GA4 tag renders. This gates `GoogleAnalytics.tsx` only —
 * it is deliberately not a gate on `trackEvent`, which reports through Google
 * Tag Manager and works whether or not the direct tag is loaded.
 */
export const analyticsEnabled = GA_MEASUREMENT_ID.length > 0;

type GtagArgs =
  | ["js", Date]
  | ["config", string, Record<string, unknown>?]
  | ["event", string, Record<string, unknown>?]
  | ["set", Record<string, unknown>];

declare global {
  interface Window {
    dataLayer?: unknown[];
    gtag?: (...args: GtagArgs) => void;
  }
}

/**
 * Send one event.
 *
 * This pushes to `window.dataLayer`, not to `window.gtag`. The difference is the
 * whole reason events work at all: the root layout loads Google Tag Manager,
 * which is what carries GA4 for this property, and `window.gtag` exists only
 * when the *direct* GA4 tag is the one loading — which it is not, by default.
 * Every event this file sent through `gtag` was therefore dropped on the floor
 * in production, silently, for as long as the events have existed.
 *
 * `dataLayer` is created by GTM's own bootstrap and is safe to push to before
 * the container has loaded; entries queued first are replayed once it does.
 *
 * A push is not the same as a measurement. GTM forwards an event to GA4 only
 * when the container holds a GA4 Event tag with a custom-event trigger for that
 * name, and GA4 counts it as a conversion only when it is marked a key event in
 * GA4 admin. Both are container-side configuration; the names below are the
 * contract with cmo-dashboard/analytics_readers.py (GA4_FUNNEL_STEPS and
 * GA4_INTENT_EVENTS), and renaming one here silently empties a console panel.
 */
export function trackEvent(name: string, params: Record<string, unknown> = {}): void {
  if (typeof window === "undefined") return;
  window.dataLayer = window.dataLayer || [];
  window.dataLayer.push({ event: name, ...params });
}

/**
 * The events the site reports, named once so a caller cannot invent a spelling
 * the dashboard does not read.
 */
export const EVENTS = {
  calculatorStart: "calculator_start",
  otpRequested: "otp_requested",
  otpVerified: "otp_verified",
  generateLead: "generate_lead",
  whatsappClick: "whatsapp_click",
  deckRequest: "deck_request",
  contactSubmit: "contact_submit",
} as const;

/** The share destinations we tag, mirrored by TRAFFIC_SOURCES in analytics_readers.py. */
export type ShareChannel = "whatsapp" | "facebook" | "x" | "linkedin" | "copy_link";

/**
 * Stamp a URL with UTM parameters so the click is attributable on arrival.
 *
 * This is not decoration. WhatsApp's in-app browser sends no referrer, so an
 * untagged share arrives in GA4 as Direct and the channel that actually earned
 * the visit gets no credit. Tagging the link is the only way to see it.
 */
export function withUtm(
  url: string,
  source: ShareChannel,
  campaign: string,
  medium = "social",
): string {
  const target = new URL(url);
  target.searchParams.set("utm_source", source);
  target.searchParams.set("utm_medium", medium);
  target.searchParams.set("utm_campaign", campaign);
  return target.toString();
}
