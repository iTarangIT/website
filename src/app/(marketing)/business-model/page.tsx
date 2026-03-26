import { createMetadata } from "@/lib/metadata";
import BusinessModelContent from "./BusinessModelContent";

export const metadata = createMetadata({
  title: "Business Model & Unit Economics",
  description:
    "Explore iTarang's fee-based TSP business model with 65-70% gross margins across four revenue streams: underwriting enablement, telemetry SaaS, collection infrastructure, and lifecycle recovery.",
  path: "/business-model",
});

export default function BusinessModelPage() {
  return <BusinessModelContent />;
}
