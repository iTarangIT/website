import type { Metadata } from "next";
import PartnerTabs from "@/components/partners/PartnerTabs";

export const metadata: Metadata = {
  title: "For Partners | iTarang",
  description:
    "Partner with iTarang — whether you're an NBFC, dealer, or OEM. Better data, better outcomes, zero blind spots.",
};

export default function ForPartnersPage() {
  return (
    <>
      {/* Hero — warm gradient with depth */}
      <section className="pt-28 pb-16 md:pt-36 md:pb-20 relative overflow-hidden">
        <div className="absolute inset-0 bg-surface-warm" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_left,rgba(5,27,154,0.06),transparent_60%)]" />
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 relative z-10">
          <span className="inline-block text-sm font-semibold text-brand-500 tracking-widest uppercase mb-4 font-sans">
            Partnerships
          </span>
          <h1 className="text-5xl md:text-7xl text-gray-900 tracking-tight leading-[1.05]">
            For Partners
          </h1>
          <p className="mt-6 text-xl text-gray-500 max-w-2xl leading-relaxed font-sans">
            Whether you lend, sell, or manufacture — we give you the data and
            tools to do it better.
          </p>
        </div>
      </section>

      <section className="bg-white px-4 py-12 md:py-16">
        <div className="mx-auto max-w-7xl">
          <h2 className="text-3xl tracking-tight text-gray-900">Explore your iTarang journey</h2>
          <p className="mt-3 max-w-2xl font-sans text-lg leading-relaxed text-gray-600">
            Start with the audience-specific information that matches your role, then use the partner overview below for the wider ecosystem context.
          </p>
          <nav aria-label="Audience solutions" className="mt-7 grid gap-4 md:grid-cols-3">
            <a href="/for-drivers" className="rounded-xl border border-gray-200 p-5 transition hover:border-brand-300 hover:bg-brand-50">
              <h3 className="text-xl text-gray-900">For Drivers</h3>
              <p className="mt-2 font-sans text-gray-600">Battery purchase, financing, monitoring, and support.</p>
            </a>
            <a href="/for-dealers" className="rounded-xl border border-gray-200 p-5 transition hover:border-brand-300 hover:bg-brand-50">
              <h3 className="text-xl text-gray-900">For Dealers</h3>
              <p className="mt-2 font-sans text-gray-600">Partnership, installation, onboarding, and service workflows.</p>
            </a>
            <a href="/for-oems" className="rounded-xl border border-gray-200 p-5 transition hover:border-brand-300 hover:bg-brand-50">
              <h3 className="text-xl text-gray-900">For OEMs</h3>
              <p className="mt-2 font-sans text-gray-600">Lifecycle, monitoring, recovery, recycling, and EPR discussions.</p>
            </a>
          </nav>
        </div>
      </section>

      <PartnerTabs />
    </>
  );
}
