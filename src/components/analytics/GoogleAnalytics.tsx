"use client";

import Script from "next/script";
import { GA_MEASUREMENT_ID, analyticsEnabled } from "@/lib/analytics";

/**
 * The GA4 tag.
 *
 * Renders nothing when NEXT_PUBLIC_GA4_MEASUREMENT_ID is unset, so the tag is
 * absent from local and preview builds rather than polluting the property.
 *
 * `afterInteractive` is deliberate: the tag is not needed to paint the page,
 * and `beforeInteractive` would put a third-party request ahead of our own
 * JavaScript on a Lighthouse run that preview_metrics.py records every cycle.
 *
 * Page views are left to GA4's own enhanced measurement, which reports the
 * path — that is the join key the dashboard uses to attribute a blog post
 * (/blog/<slug>) against Search Console's page dimension.
 *
 * The root layout also loads Google Tag Manager (GTM-NWF4GDVS). Only one of the
 * two may configure GA4 for a given property: if the container already holds a
 * GA4 configuration tag for this measurement id, setting
 * NEXT_PUBLIC_GA4_MEASUREMENT_ID as well double-counts every page view. That is
 * why the id is unset by default and this renders nothing. Turning it on is a
 * decision about the container, not just about this file — and note that
 * ShareBar's `share` events go through `window.gtag`, which only exists when
 * this tag is the one loading GA4.
 */
export default function GoogleAnalytics() {
  if (!analyticsEnabled) return null;

  return (
    <>
      <Script
        src={`https://www.googletagmanager.com/gtag/js?id=${GA_MEASUREMENT_ID}`}
        strategy="afterInteractive"
      />
      <Script id="ga4-init" strategy="afterInteractive">
        {`window.dataLayer = window.dataLayer || [];
function gtag(){dataLayer.push(arguments);}
gtag('js', new Date());
gtag('config', '${GA_MEASUREMENT_ID}');`}
      </Script>
    </>
  );
}
