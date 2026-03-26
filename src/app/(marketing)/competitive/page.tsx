import { createMetadata } from "@/lib/metadata";
import CompetitiveContent from "./CompetitiveContent";

export const metadata = createMetadata({
  title: "Competitive Landscape",
  description:
    "See how iTarang compares as the only full-lifecycle Technology Service Provider in the EV battery financing ecosystem.",
  path: "/competitive",
});

export default function CompetitivePage() {
  return <CompetitiveContent />;
}
