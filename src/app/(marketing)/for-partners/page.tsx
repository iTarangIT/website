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

      <PartnerTabs />
    </>
  );
}
