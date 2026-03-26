import { createMetadata } from "@/lib/metadata";
import CTASection from "@/components/shared/CTASection";
import SolutionsHero from "@/components/solutions/SolutionsHero";
import SolutionsPillarsSection from "@/components/solutions/SolutionsPillarsSection";
import WorkflowAnimation from "@/components/solutions/WorkflowAnimation";
import FleetDashboardWidget from "@/components/dashboard-widget/FleetDashboardWidget";

export const metadata = createMetadata({
  title: "Platform & Solutions",
  description:
    "Smart Battery Telemetry, Intelligent Risk Evaluation, and Lifecycle Asset Management — the three pillars that make EV batteries bankable, trackable, and recoverable.",
  path: "/solutions",
});

export default function SolutionsPage() {
  return (
    <>
      {/* Hero Section */}
      <SolutionsHero />

      {/* Three Pillars — alternating layout */}
      <SolutionsPillarsSection />

      {/* Operational Workflow */}
      <WorkflowAnimation />

      {/* Live Fleet Dashboard */}
      <FleetDashboardWidget />

      {/* CTA */}
      <CTASection
        title="See the Platform in Action"
        subtitle="Schedule a live walkthrough with our team and see how iTarang transforms battery financing."
        primaryCTA={{ label: "Book a Demo", href: "/contact" }}
        secondaryCTA={{
          label: "Download Platform Overview",
          href: "/resources/platform-overview.pdf",
        }}
      />
    </>
  );
}
