import { createMetadata } from "@/lib/metadata";
import RegulatoryContent from "./RegulatoryContent";

export const metadata = createMetadata({
  title: "Regulatory Moat",
  description:
    "How iTarang leverages EPR mandates, DPDP compliance, and TSP positioning to create a deep regulatory moat in EV battery lifecycle management.",
  path: "/regulatory",
});

export default function RegulatoryPage() {
  return <RegulatoryContent />;
}
