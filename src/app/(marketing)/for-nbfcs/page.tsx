import { createMetadata } from "@/lib/metadata";
import PainPointsSection from "@/components/nbfc/PainPointsSection";
import WorkflowSteps from "@/components/nbfc/WorkflowSteps";
import DataFlywheelAnimation from "@/components/nbfc/DataFlywheelAnimation";
import RiskFeatures from "@/components/nbfc/RiskFeatures";
import NBFCRevenueModel from "@/components/nbfc/NBFCRevenueModel";
import CompetitivePosition from "@/components/nbfc/CompetitivePosition";
import NBFCContactCTA from "@/components/nbfc/NBFCContactCTA";
import FleetDashboardWidget from "@/components/dashboard-widget/FleetDashboardWidget";

export const metadata = createMetadata({
  title: "For NBFCs",
  description:
    "Make EV batteries bankable with real-time SOH data, behavioral risk scoring, remote immobilisation, and end-to-end lifecycle management. Reduce NPAs from 8-12% to under 2%.",
  path: "/for-nbfcs",
});

export default function ForNBFCsPage() {
  return (
    <>
      {/* Hero / Pain Point — dark immersive opening */}
      <PainPointsSection />

      {/* End-to-end workflow */}
      <WorkflowSteps />

      {/* Data flywheel animation */}
      <DataFlywheelAnimation />

      {/* Risk mitigation features grid */}
      <RiskFeatures />

      {/* Revenue / economics comparison */}
      <NBFCRevenueModel />

      {/* Live fleet dashboard demo */}
      <FleetDashboardWidget />

      {/* TSP positioning */}
      <CompetitivePosition />

      {/* Contact CTA */}
      <NBFCContactCTA />
    </>
  );
}
