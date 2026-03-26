import type { Metadata } from "next";
import { createMetadata } from "@/lib/metadata";
import SectionHeading from "@/components/shared/SectionHeading";
import FadeInOnScroll from "@/components/shared/FadeInOnScroll";
import OpportunitySection from "@/components/investors/OpportunitySection";
import ProblemCards from "@/components/investors/ProblemCards";
import SolutionPillars from "@/components/investors/SolutionPillars";
import BusinessModelTable from "@/components/investors/BusinessModelTable";
import UnitEconomicsCard from "@/components/investors/UnitEconomicsCard";
import TractionMetrics from "@/components/investors/TractionMetrics";
import TeamSection from "@/components/investors/TeamSection";
import TheAskSection from "@/components/investors/TheAskSection";
import InvestorCTA from "@/components/investors/InvestorCTA";

export const metadata: Metadata = createMetadata({
  title: "For Investors",
  description:
    "Invest in India's first EV Battery Financing & Lifecycle Management platform. ₹11,250 Cr TAM, 65-70% gross margins, pre-seed equity round of ₹8 Crore. Discover the iTarang opportunity.",
  path: "/for-investors",
});

export default function ForInvestorsPage() {
  return (
    <>
      {/* Hero Banner */}
      <section className="relative overflow-hidden bg-brand-900 py-24 md:py-32">
        {/* Subtle background pattern */}
        <div
          className="absolute inset-0 opacity-10"
          style={{
            backgroundImage:
              "radial-gradient(circle at 1px 1px, rgba(255,255,255,0.3) 1px, transparent 0)",
            backgroundSize: "32px 32px",
          }}
        />
        {/* Gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-br from-brand-900 via-brand-900 to-brand-800" />

        <div className="relative mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 text-center">
          <FadeInOnScroll>
            <SectionHeading
              badge="For Investors"
              title="The Opportunity"
              subtitle="India's EV battery economy is a ₹11,250 Cr annual market with no intelligence layer. iTarang is building the infrastructure to make batteries bankable, trackable, and programmable."
              dark
            />
          </FadeInOnScroll>
        </div>
      </section>

      {/* Section 2: Market Opportunity Stats */}
      <OpportunitySection />

      {/* Section 3: Problem Cards */}
      <ProblemCards />

      {/* Section 4: Solution Pillars */}
      <SolutionPillars />

      {/* Section 5: Business Model */}
      <BusinessModelTable />

      {/* Section 6: Unit Economics */}
      <UnitEconomicsCard />

      {/* Section 7: Traction & Validation */}
      <TractionMetrics />

      {/* Section 8: Team */}
      <TeamSection />

      {/* Section 9: The Ask */}
      <TheAskSection />

      {/* Section 10: Investor CTA */}
      <InvestorCTA />
    </>
  );
}
