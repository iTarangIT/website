import Link from "next/link";
import { createMetadata } from "@/lib/metadata";
import BlogLayout from "@/components/blog/BlogLayout";

export const metadata = createMetadata({
  title: "E-Rickshaw Battery Maintenance Alerts: Troubleshooting FAQ",
  description:
    "Understand e-rickshaw battery health, charging, temperature, and range alerts, complete safe driver and dealer checks, and learn when to contact iTarang support.",
  path: "/blog/e-rickshaw-battery-maintenance-alerts-troubleshooting",
});

export default function ERickshawBatteryMaintenanceAlertsArticle() {
  return (
    <BlogLayout
      title="E-Rickshaw Battery Maintenance Alerts and Troubleshooting FAQ"
      date="2026-07-27"
      readTime="8 min read"
      category="charging-maintenance"
    >
      <p>
        A battery alert is a signal to investigate, not a diagnosis by itself. This guide
        explains the battery information iTarang describes, the safe checks a driver can make,
        and the information to collect before asking a dealer or service team for help.
      </p>

      <h2>Quick Triage: What Kind of Alert Are You Seeing?</h2>
      <p>Start by noting which of these best describes the issue:</p>
      <ul>
        <li>A battery-health or State of Health (SOH) warning.</li>
        <li>A low or unexpected State of Charge (SOC) reading.</li>
        <li>A temperature alert or unusual heat.</li>
        <li>Charging that stops, behaves abnormally, or repeatedly interrupts.</li>
        <li>A deep-discharge pattern, reduced range, or another anomaly alert.</li>
        <li>Battery, location, or dashboard data that is missing or contradictory.</li>
      </ul>
      <p>
        If there is visible damage, smoke, an unusual smell or heat, water or impact damage, or
        an otherwise unsafe charging condition, stop using the equipment and escalate through the
        approved support route. Do not attempt an electrical repair or continue with a visibly
        damaged battery.
      </p>

      <h2>What the Battery Signals Tell You</h2>
      <p>
        SOH is a longer-term battery-health indicator, while SOC describes the current charge
        state. Temperature is an observation about operating conditions, and charge cycles help
        show charging and usage history. Anomaly alerts identify an irregularity for review.
      </p>
      <p>
        iTarang describes monitoring of SOH, SOC, location, temperature, and charge cycles, along
        with early-warning signals such as temperature spikes, deep-discharge patterns, and
        abnormal charge cycles. A displayed signal does not, by itself, confirm a failure, and
        there is no universal numeric threshold in this guide for diagnosing one.
      </p>

      <h2>Basic Driver Checks</h2>
      <ol>
        <li>Record the exact alert, the time, and the SOC, SOH, or temperature shown.</li>
        <li>Note whether the warning or symptom repeats after the vehicle is parked safely.</li>
        <li>Check the charger connection and indicator behavior from outside the equipment.</li>
        <li>Look for visible cable, connector, water, or impact damage without opening the pack.</li>
        <li>Record recent charging, route, payload, weather, and other relevant operating context.</li>
      </ol>
      <p>
        Do not open the battery pack, alter wiring, bypass protections, substitute an unverified
        charger, or experiment with a battery that is hot or visibly damaged.
      </p>

      <h2>Charging Interruptions and Abnormal Charging</h2>
      <p>
        Separate a one-time interruption from a recurring abnormal charge-cycle pattern. Record
        what the charger indicator showed, what appeared in the monitoring view, when charging
        stopped, and whether the event happened again. A reconnection or restart should not be
        treated as a guaranteed fix.
      </p>
      <p>
        Repeated interruptions, an anomaly alert, visible damage, or an unsafe charging condition
        should be escalated to the dealer or service team with the recorded details.
      </p>

      <h2>Temperature Alerts, Deep Discharge, and Reduced Range</h2>
      <p>
        Temperature spikes and deep-discharge patterns are monitoring signals that help the team
        review what happened. They are not, on their own, a safe temperature limit or a confirmed
        cause of a range change. Record the route, load, operating conditions, recent charging,
        visible SOC or SOH, and charge-cycle history where available.
      </p>
      <p>
        Reduced range can have more than one explanation. If the change persists, is accompanied
        by an alert, or cannot be explained by the operating context, ask a dealer or iTarang to
        review it rather than assuming a cause.
      </p>

      <h2>Dealer Checks and Case Preparation</h2>
      <p>
        A dealer can gather the vehicle and battery identity, dashboard or IoT visibility, alert
        history, timestamps, charger and installation context, and whether the issue recurs. The
        available SOH, SOC, temperature, location, charge-cycle, and anomaly data can then be
        compared with the reported symptom through the approved workflow.
      </p>
      <p>
        Dealers should not reset or bypass protections, alter telemetry, make a warranty decision,
        replace parts, or promise an outcome outside the approved process.
      </p>

      <h2>When to Involve iTarang or the Service Team</h2>
      <p>
        Request support for persistent or repeated alerts, missing or contradictory data,
        abnormal charging, temperature concerns, deep-discharge patterns, materially reduced
        range, failed pairing or activation, or any safety concern. Use the owner-approved route
        to the nearest service point; availability and geographic coverage should be confirmed for
        the specific case.
      </p>
      <p>
        An alert does not automatically determine warranty coverage or replacement. Those policy
        questions belong to the approved warranty and support process.
      </p>

      <h2>What to Include in an Escalation</h2>
      <ul>
        <li>Your driver, dealer, or fleet role and city.</li>
        <li>Vehicle and battery identifiers, if available.</li>
        <li>The exact alert text, timestamp, and whether dashboard data was visible.</li>
        <li>Recent charging details, route or load context, and observed symptoms.</li>
        <li>Photos only when it is safe to take them, plus your preferred contact route.</li>
      </ul>
      <p>
        For lifecycle-monitoring context, read <Link href="/how-it-works">How It Works</Link>.
        Dealers and workshops can review <Link href="/for-partners">For Partners</Link>. For an
        owner-approved escalation, use <Link href="/contact">Contact</Link> and include your city
        and the relevant alert details.
      </p>
    </BlogLayout>
  );
}
