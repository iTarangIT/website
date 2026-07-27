import type { Metadata } from "next";
import Link from "next/link";
import Button from "@/components/ui/Button";

export const metadata: Metadata = {
  title: "E-Rickshaw Battery Warranty, Service and Replacement Support | iTarang",
  description:
    "Learn what to prepare for e-rickshaw battery service support, how battery alerts inform triage, and which warranty or replacement details must be confirmed with iTarang.",
};

const caseDetails = [
  "Your driver, owner, dealer, or fleet role and city",
  "Vehicle, battery, and IoT identifiers, if available",
  "The exact alert text, timestamp, and visible SOH, SOC, or temperature",
  "Recent charging, route, payload, and operating context",
  "Photos only when it is safe to take them, plus your preferred contact route",
];

const policyQuestions = [
  "Warranty duration and start date",
  "Eligible products and purchasers",
  "Covered conditions, exclusions, and required documents",
  "Service channels, geographic coverage, and response expectations",
  "Replacement, refund, buyback, valuation, fees, stock, and transport terms",
];

export default function ERickshawBatteryWarrantySupportPage() {
  return (
    <main className="font-sans">
      <section className="bg-brand-950 py-20 text-white md:py-28">
        <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
          <p className="mb-4 text-sm font-semibold uppercase tracking-[0.2em] text-brand-300">
            Owner support
          </p>
          <h1 className="max-w-3xl text-4xl font-bold tracking-tight sm:text-5xl">
            E-Rickshaw Battery Warranty, Service and Replacement Support
          </h1>
          <p className="mt-6 max-w-2xl text-lg leading-8 text-brand-100/80">
            Need help after purchase? Prepare the details below so iTarang or an approved service
            team can review the battery concern and confirm the right next step.
          </p>
          <div className="mt-8 flex flex-wrap gap-4">
            <Button href="/contact" size="lg">
              Contact iTarang
            </Button>
            <Button
              href="/blog/e-rickshaw-battery-maintenance-alerts-troubleshooting"
              size="lg"
              variant="outline"
              className="border-white/30 text-white hover:bg-white/10"
            >
              Review alert guidance
            </Button>
          </div>
        </div>
      </section>

      <section className="bg-brand-50 py-12 md:py-16">
        <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
          <div className="rounded-2xl border border-amber-200 bg-amber-50 p-6 text-amber-950">
            <h2 className="text-xl font-semibold">An alert is not a warranty decision</h2>
            <p className="mt-3 leading-7">
              SOH, SOC, temperature, charge-cycle history, and anomaly alerts can help inform
              triage. They do not, by themselves, confirm battery failure, warranty eligibility,
              replacement, or buyback. Follow the approved support workflow for diagnosis.
            </p>
          </div>
        </div>
      </section>

      <section className="bg-white py-16 md:py-24">
        <div className="mx-auto grid max-w-5xl gap-12 px-4 sm:px-6 lg:grid-cols-2 lg:px-8">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-brand-500">
              Before requesting service
            </p>
            <h2 className="mt-3 text-3xl font-bold tracking-tight text-gray-900">
              Prepare the case details
            </h2>
            <p className="mt-4 leading-7 text-gray-600">
              Share only information that is safe and available to you. A complete evidence pack
              helps the support team understand the alert, symptom, and operating context.
            </p>
            <ul className="mt-6 space-y-4 text-gray-600">
              {caseDetails.map((detail) => (
                <li key={detail} className="flex gap-3">
                  <span className="font-bold text-brand-500">•</span>
                  <span>{detail}</span>
                </li>
              ))}
            </ul>
          </div>
          <div className="rounded-2xl border border-gray-200 bg-gray-50 p-7">
            <h2 className="text-2xl font-bold text-gray-900">Safe escalation</h2>
            <p className="mt-4 leading-7 text-gray-600">
              If there is visible damage, smoke, unusual heat or smell, water or impact damage, or
              another unsafe charging condition, stop using the equipment and use the approved
              support route. Do not open, bypass, reset, or self-repair the battery pack.
            </p>
            <p className="mt-4 leading-7 text-gray-600">
              For general explanations of battery signals and safe observations, read the
              maintenance-alert troubleshooting guide.
            </p>
            <Link
              className="mt-5 inline-block font-semibold text-brand-600 hover:text-brand-800"
              href="/blog/e-rickshaw-battery-maintenance-alerts-troubleshooting"
            >
              Read the alert guide →
            </Link>
          </div>
        </div>
      </section>

      <section className="bg-gray-50 py-16 md:py-24">
        <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-brand-500">
            Policy review
          </p>
          <h2 className="mt-3 max-w-3xl text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
            What the support team must confirm
          </h2>
          <p className="mt-4 max-w-3xl leading-7 text-gray-600">
            Warranty, service, replacement, and buyback terms depend on the owner-approved product
            and operating policy. Do not infer these details from general lithium-battery practice.
          </p>
          <div className="mt-8 overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm">
            <ul className="divide-y divide-gray-200">
              {policyQuestions.map((question) => (
                <li key={question} className="px-6 py-5 text-gray-700">
                  <span className="font-semibold text-gray-900">To be confirmed:</span> {question}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      <section className="bg-white py-16 md:py-24">
        <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold tracking-tight text-gray-900">Common questions</h2>
          <div className="mt-8 grid gap-6 md:grid-cols-2">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">How do I request service?</h3>
              <p className="mt-2 leading-7 text-gray-600">
                Use the approved driver, owner, dealer, or fleet contact route and include the case
                details above. The team will confirm the applicable workflow.
              </p>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Does an alert mean I need a replacement?</h3>
              <p className="mt-2 leading-7 text-gray-600">
                No. An alert informs review and triage; an approved service process must determine
                diagnosis, warranty eligibility, and any replacement next step.
              </p>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">How do I find the nearest service point?</h3>
              <p className="mt-2 leading-7 text-gray-600">
                Contact iTarang with your city and case details. Service-point availability and
                geographic coverage must be confirmed for the specific case.
              </p>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Can I request a buyback?</h3>
              <p className="mt-2 leading-7 text-gray-600">
                Ask the support team about the approved lifecycle workflow. Eligibility, valuation,
                fees, and any return or recycling terms must be confirmed before an outcome is promised.
              </p>
            </div>
          </div>
          <div className="mt-10 flex flex-wrap gap-3">
            <Button href="/contact">Start a support enquiry</Button>
            <Button href="/how-it-works" variant="secondary">Learn how monitoring works</Button>
          </div>
        </div>
      </section>
    </main>
  );
}
