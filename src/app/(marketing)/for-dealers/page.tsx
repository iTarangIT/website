import AudienceLandingPage from "@/components/partners/AudienceLandingPage";
import DealerNetworkMap from "@/components/partners/dealer-map/DealerNetworkMap";
import { getDealerLocations } from "@/lib/dealers/locations";
import { createMetadata } from "@/lib/metadata";

export const metadata = createMetadata({
  title: "E-Rickshaw Battery Dealer Partnership and Financing — iTarang",
  description:
    "Partner with iTarang to offer e-rickshaw battery solutions, financing support, installation workflow, and dealer assistance in India.",
  path: "/for-dealers",
});

// The dealer map reads the CRM database at request time (cached for an hour
// in getDealerLocations). Rendering per request also keeps `next build` from
// touching the database, where DATABASE_URL is only a placeholder.
export const dynamic = "force-dynamic";

export default async function ForDealersPage() {
  const locations = await getDealerLocations();

  return (
    <AudienceLandingPage
      page={{
        eyebrow: "For Dealers",
        title: "Partner with iTarang as an E-Rickshaw Battery Dealer",
        intro:
          "Discuss a dealer workflow for battery enquiries, financing support, installation, monitoring, and service. The partnership team will confirm the products, responsibilities, and geography relevant to your business.",
        // Rendered even when the CRM is unreachable and `locations` is null: the
        // component drops the map card but keeps the nearest-dealer search,
        // which reads the database on its own and may well succeed.
        afterHero: <DealerNetworkMap locations={locations ?? []} />,
        sections: [
          {
            title: "What the partnership can cover",
            body: (
              <p>
                Use this page to start a conversation about the approved product range, financing support, sales enablement, installation, monitoring, service, and territory terms. Specific benefits and availability must be confirmed by iTarang.
              </p>
            ),
          },
          {
            title: "How the workflows connect",
            body: (
              <p>
                A typical discussion can cover enquiry, driver assessment, financing, installation or activation, and ongoing support. The team will clarify lead handling, documentation, and handoffs for your proposed partnership.
              </p>
            ),
          },
          {
            title: "Installation and activation",
            body: (
              <p>
                Dealer responsibilities for fitting, battery or IoT pairing, activation, and customer handoff depend on the approved operating workflow. Confirm the required tools, training, and support before onboarding.
              </p>
            ),
          },
          {
            title: "Support and service escalation",
            body: (
              <p>
                Ask about service points, training, escalation routes, geographic coverage, and response expectations. Only the support level agreed for your partnership should be represented to customers.
              </p>
            ),
          },
          {
            title: "Commercial and eligibility questions",
            body: (
              <ul className="list-disc space-y-2 pl-5">
                <li>What documentation and onboarding steps are required?</li>
                <li>How are lead ownership, economics, and risk responsibilities handled?</li>
                <li>Which products, locations, and installation capabilities are currently supported?</li>
              </ul>
            ),
          },
          {
            title: "Start a dealer conversation",
            body: (
              <p>
                Share your dealership, location, customer profile, and the support you need. The team can then confirm an appropriate qualification and onboarding path without promising unverified margins, approval rates, or timelines.
              </p>
            ),
          },
        ],
        primaryCta: "Become a dealer partner",
        primaryHref: "/contact?role=dealer",
        secondaryCta: "View partner overview",
        secondaryHref: "/for-partners",
      }}
    />
  );
}
