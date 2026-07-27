import type { Metadata } from "next";
import Link from "next/link";
import Button from "@/components/ui/Button";
import { SEED } from "@/lib/calculator/engine";

export const metadata: Metadata = {
  title: "E-Rickshaw Lithium Battery Models and Specifications | iTarang",
  description:
    "Compare iTarang e-rickshaw lithium battery options by verified voltage and Ah capacity before choosing in the calculator.",
};

type BatteryOption = {
  model: string;
  voltage: string;
  capacity: string;
};

const batteryOptions: BatteryOption[] = Object.keys(
  (SEED as unknown as { Bajaj: { modelCaps: Record<string, number> } }).Bajaj.modelCaps,
)
  .map((model) => {
    const match = model.match(/^([0-9.]+V)\s*-\s*([0-9]+)\s*AMP/);
    if (!match) return null;
    return {
      model,
      voltage: match[1],
      capacity: `${match[2]} Ah`,
    };
  })
  .filter((option): option is BatteryOption => option !== null);

const voltageGroups = ["51.2V", "60.8V", "64V", "73.6V"];

export default function ERickshawBatteryModelsSpecificationsPage() {
  return (
    <main className="font-sans">
      <section className="bg-brand-950 py-20 text-white md:py-28">
        <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
          <p className="mb-4 text-sm font-semibold uppercase tracking-[0.2em] text-brand-300">
            Battery selection guide
          </p>
          <h1 className="max-w-3xl text-4xl font-bold tracking-tight sm:text-5xl">
            E-Rickshaw Lithium Battery Models and Specifications
          </h1>
          <p className="mt-6 max-w-2xl text-lg leading-8 text-brand-100/80">
            Compare the model and capacity choices currently displayed by the financing calculator,
            then confirm vehicle compatibility before selecting an option.
          </p>
          <div className="mt-8 flex flex-wrap gap-4">
            <Button href="/how-it-works" size="lg">
              Check current options in the calculator
            </Button>
            <Button
              href="/contact"
              size="lg"
              variant="outline"
              className="border-white/30 text-white hover:bg-white/10"
            >
              Ask about compatibility
            </Button>
          </div>
        </div>
      </section>

      <section className="bg-brand-50 py-12 md:py-16">
        <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
          <div className="rounded-2xl border border-amber-200 bg-amber-50 p-6 text-amber-950">
            <h2 className="text-xl font-semibold">Use voltage as a comparison field, not a fitment guarantee</h2>
            <p className="mt-3 leading-7">
              A battery must match the vehicle and its electrical system. Confirm the controller,
              charger, connector, dimensions, installation requirements, and dealer assessment
              before making a selection. Do not substitute one voltage for another based on this
              table alone.
            </p>
          </div>
        </div>
      </section>

      <section className="bg-white py-16 md:py-24">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
          <div className="max-w-2xl">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-brand-500">Verified calculator choices</p>
            <h2 className="mt-3 text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
              Compare models by voltage and Ah capacity
            </h2>
            <p className="mt-4 leading-7 text-gray-600">
              These model labels and voltage buckets are taken from the calculator configuration.
              Intended use, compatibility, price, financing eligibility, warranty, availability,
              range, and cycle-life claims require confirmation for the current enquiry.
            </p>
          </div>

          <div className="mt-10 overflow-hidden rounded-2xl border border-gray-200 shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[760px] border-collapse text-left text-sm">
                <caption className="sr-only">Current calculator battery model choices grouped by voltage</caption>
                <thead className="bg-brand-950 text-white">
                  <tr>
                    <th className="px-5 py-4 font-semibold">Voltage</th>
                    <th className="px-5 py-4 font-semibold">Ah capacity</th>
                    <th className="px-5 py-4 font-semibold">Calculator model</th>
                    <th className="px-5 py-4 font-semibold">Use, compatibility, and financing</th>
                  </tr>
                </thead>
                <tbody>
                  {voltageGroups.flatMap((voltage) =>
                    batteryOptions
                      .filter((option) => option.voltage === voltage)
                      .map((option) => (
                        <tr key={option.model} className="border-t border-gray-200 align-top even:bg-gray-50">
                          <td className="px-5 py-4 font-semibold text-gray-900">{option.voltage}</td>
                          <td className="px-5 py-4 text-gray-700">{option.capacity}</td>
                          <td className="px-5 py-4 text-gray-900">{option.model}</td>
                          <td className="px-5 py-4 text-gray-600">
                            <span className="block">Use case: confirm with the owner or dealer.</span>
                            <span className="mt-1 block">Compatibility: vehicle and system assessment required.</span>
                            <Link className="mt-1 inline-block font-semibold text-brand-600 hover:text-brand-800" href="/how-it-works">
                              Financing path: use How It Works calculator
                            </Link>
                          </td>
                        </tr>
                      )),
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </section>

      <section className="bg-gray-50 py-16 md:py-24">
        <div className="mx-auto grid max-w-5xl gap-12 px-4 sm:px-6 lg:grid-cols-2 lg:px-8">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-brand-500">Before you choose</p>
            <h2 className="mt-3 text-3xl font-bold tracking-tight text-gray-900">Bring the right compatibility details</h2>
            <ul className="mt-6 space-y-4 text-gray-600">
              <li>• Vehicle make, model, system voltage, and current battery details.</li>
              <li>• Controller, charger, connector, mounting space, and dimensions.</li>
              <li>• Route, payload, driving pattern, and charging access.</li>
              <li>• City and the authorised dealer or engineering contact for assessment.</li>
            </ul>
          </div>
          <div className="rounded-2xl border border-gray-200 bg-white p-7 shadow-sm">
            <h2 className="text-2xl font-bold text-gray-900">What is not stated here</h2>
            <p className="mt-4 leading-7 text-gray-600">
              Range, cycle life, charge time, price, EMI, lender, tenure, eligibility, warranty,
              availability, and installation promises are not inferred from a model label. Confirm
              each claim from the current owner-approved catalogue or calculator result.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <Button href="/how-it-works">See How It Works</Button>
              <Button href="/contact" variant="secondary">Contact iTarang</Button>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
