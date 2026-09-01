"use client";

import { useEffect } from "react";
import { EVENTS, trackEvent } from "@/lib/analytics";

/**
 * Reports every outbound WhatsApp click.
 *
 * One delegated listener rather than an onClick on each button. There are six
 * WhatsApp CTAs across the site in five differently-shaped components — a
 * `motion.a`, a plain anchor, two entries in data arrays passed to presentational
 * components, a role-prefilled deeplink list — and wiring each one would mean
 * six places to keep in step and a seventh that gets added later without a
 * handler. A click on an anchor is a click on an anchor wherever it lives.
 *
 * WhatsApp is the highest-intent action the site offers: it is the de facto lead
 * channel, and until now not one of those six clicks was measured.
 *
 * `location` distinguishes them, because "the floating button gets all the taps
 * and the contact page gets none" is the finding that changes a layout. It comes
 * from an explicit `data-wa-location` where a component sets one, and otherwise
 * from the landmark the anchor sits in — a fallback that degrades to something
 * true rather than to nothing.
 */
function locationOf(anchor: HTMLAnchorElement): string {
  const explicit = anchor.dataset.waLocation;
  if (explicit) return explicit;
  if (anchor.closest("footer")) return "footer";
  if (anchor.closest("header")) return "header";
  if (anchor.closest("nav")) return "nav";
  if (getComputedStyle(anchor).position === "fixed") return "floating";
  return "body";
}

export default function WhatsAppTracker() {
  useEffect(() => {
    function onClick(event: MouseEvent) {
      const target = event.target;
      if (!(target instanceof Element)) return;
      const anchor = target.closest("a");
      if (!anchor) return;
      // Read the attribute, not the resolved property: a relative href would
      // resolve against the current origin and never match.
      const href = anchor.getAttribute("href") || "";
      if (!/^https?:\/\/(api\.whatsapp\.com|wa\.me)\//i.test(href)) return;
      trackEvent(EVENTS.whatsappClick, {
        location: locationOf(anchor),
        page_path: window.location.pathname,
      });
    }
    // Capture phase: some of these anchors sit inside components that stop
    // propagation on their own wrappers, and a bubble-phase listener on
    // document would never see those clicks.
    document.addEventListener("click", onClick, { capture: true });
    return () => document.removeEventListener("click", onClick, { capture: true });
  }, []);

  return null;
}
