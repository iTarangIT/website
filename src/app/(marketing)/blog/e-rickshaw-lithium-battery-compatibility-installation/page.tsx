import Link from "next/link";
import { createMetadata } from "@/lib/metadata";
import BlogLayout from "@/components/blog/BlogLayout";

export const metadata = createMetadata({
  title: "E-Rickshaw Lithium Battery Compatibility and Installation Guide",
  description:
    "Learn what to check before choosing an e-rickshaw lithium battery, including vehicle compatibility, model selection, dealer installation, IoT pairing, activation, and safety checks.",
  path: "/blog/e-rickshaw-lithium-battery-compatibility-installation",
});

export default function ERickshawBatteryCompatibilityInstallationArticle() {
  return (
    <BlogLayout
      title="How to Check E-Rickshaw Lithium Battery Compatibility and Installation Requirements"
      slug="e-rickshaw-lithium-battery-compatibility-installation"
      date="2026-07-24"
      readTime="7 min read"
      category="battery-selection"
    >
      <p>
        Choosing a lithium battery for an e-rickshaw starts with compatibility, not just
        capacity or price. The right option depends on the vehicle, its electrical system,
        the available installation space, and the support available in your city. This guide
        outlines the information to prepare before speaking with an authorised dealer.
      </p>

      <h2>What to Confirm Before Choosing a Battery</h2>
      <p>Prepare as much of the following information as you can:</p>
      <ul>
        <li>Vehicle make, model, and vehicle or chassis details, if available.</li>
        <li>The current battery type and the voltage shown on the vehicle or battery label.</li>
        <li>Battery-compartment space, access, mounting points, and any visible connector or wiring details.</li>
        <li>Charger details and how the vehicle is used, including route, payload, and charging access.</li>
        <li>Your city, so the appropriate sales or service path can be confirmed.</li>
      </ul>
      <p>
        Do not rely on a visual match or alter wiring before a dealer confirms compatibility.
        If any vehicle information is missing, ask for an assessment before selecting a model.
      </p>

      <h2>How Compatibility Is Checked</h2>
      <p>
        A compatibility review should cover four separate questions: does the battery match the
        vehicle&apos;s electrical system, can it be physically placed and secured, are the connectors
        and charger suitable, and is installation and service support available for the vehicle
        in your location? Exact vehicle lists, voltage mappings, connector requirements, and
        approved fitment rules should come from the current product team or authorised dealer.
      </p>

      <h2>Choosing the Voltage and Battery Model</h2>
      <p>
        iTarang presents battery-model and voltage choices through its product and financing
        journeys. The correct choice must follow the vehicle assessment and the approved product
        catalogue. Do not infer range, charging time, dimensions, weight, life, or performance
        from a label or from a model name alone.
      </p>
      <p>
        Once compatibility is confirmed, visit <Link href="/how-it-works">How It Works</Link> to
        understand the product and financing journey, then use the <Link href="/how-it-works">EMI
        calculator</Link> to review an estimate.
      </p>

      <h2>What Dealer Installation Covers</h2>
      <p>
        Installation normally begins with an inspection and confirmation of the approved battery
        option. The dealer can then explain safe removal or isolation of the existing battery,
        placement and securing, cable and connector checks, charger compatibility, and the
        handover checks required before use.
      </p>
      <p>
        Installation time, included parts, doorstep availability, and the exact process vary by
        vehicle and location. Confirm those details with the dealer rather than relying on a
        fixed promise.
      </p>

      <h2>Battery and IoT-Device Pairing</h2>
      <p>
        Pairing associates the installed battery and its IoT device with the relevant vehicle or
        account so that the intended monitoring workflow can be used. The dealer should confirm
        the information needed for pairing and explain the approved steps. Do not share credentials
        with an unauthorised person or invent app, network, or diagnostic requirements that have
        not been provided by iTarang.
      </p>

      <h2>Activation After Installation</h2>
      <p>
        The installation journey describes activation as taking up to 24 hours. Confirm with the
        dealer whether that is a maximum, an expected timeframe, or a service commitment for your
        installation. If the battery or status is not visible after the confirmed window, record
        the installation details and contact the support path provided by the dealer.
      </p>

      <h2>Safety Checks Before the First Trip</h2>
      <p>Before leaving the installation point, ask the dealer to confirm that:</p>
      <ul>
        <li>The battery is secured and the cables and connectors are protected.</li>
        <li>The charger and relevant indicators behave as expected.</li>
        <li>There is no visible damage, unusual heat, or unusual smell.</li>
        <li>You understand the approved charging and escalation steps.</li>
      </ul>
      <p>
        Do not attempt electrical repairs or continue using equipment that appears damaged. Stop
        and ask an authorised dealer for help if the voltage is uncertain, the battery does not
        fit, the charger or connector seems mismatched, pairing fails, activation is missing, or
        you see a warning, unusual heat, smell, water damage, or impact damage.
      </p>

      <h2>Where to Get Help</h2>
      <p>
        Dealers and workshop or OEM partners can use the <Link href="/for-partners">For Partners</Link>
        page for partnership context. For a compatibility review or installation question, use
        <Link href="/contact"> Contact</Link> and select your city so the appropriate path can be
        confirmed. Keep model-specific specifications, warranty terms, availability, and service
        coverage tied to the current approved product information.
      </p>

      <h2>Related Resources</h2>
      <ul>
        <li><Link href="/how-it-works">How It Works</Link> for the product and financing journey.</li>
        <li><Link href="/how-it-works">EMI calculator</Link> for an estimate after compatibility is confirmed.</li>
        <li><Link href="/for-partners">For Partners</Link> for dealer, workshop, and OEM context.</li>
        <li><Link href="/contact">Contact</Link> for an owner-approved compatibility or service enquiry.</li>
      </ul>
    </BlogLayout>
  );
}
