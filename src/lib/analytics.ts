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

/** The tag only loads when a measurement id is configured. */
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
 * Send one GA4 event. Safe to call before the tag has loaded, on the server,
 * and when analytics is switched off — it simply does nothing.
 */
export function trackEvent(name: string, params: Record<string, unknown> = {}): void {
  if (typeof window === "undefined" || !analyticsEnabled) return;
  window.gtag?.("event", name, params);
}

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
