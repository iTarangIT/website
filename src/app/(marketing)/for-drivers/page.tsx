import AudienceLandingPage from "@/components/partners/AudienceLandingPage";
import { createMetadata } from "@/lib/metadata";

export const metadata = createMetadata({
  title: "E-Rickshaw Battery Finance and Support for Drivers in India — iTarang",
  description:
    "Explore iTarang e-rickshaw battery purchase and financing options, monitoring, service support, and the next step for drivers in India.",
  path: "/for-drivers",
});

export default function ForDriversPage() {
  return (
    <AudienceLandingPage
      page={{
        eyebrow: "For Drivers",
        title: "E-Rickshaw Battery Solutions for Drivers in India",
        intro:
          "Find a practical route to understand battery options, financing questions, monitoring, and service support. Share your vehicle and city details so the right next step can be confirmed with you.",
        sections: [
          {
            title: "Choose a battery with the right information",
            body: (
              <p>
                Start with the existing product and compatibility information. Battery model, voltage, Ah, installation responsibility, and availability should be confirmed for your vehicle before purchase.
              </p>
            ),
          },
          {
            title: "Understand the financing path",
            body: (
              <p>
                Use the approved calculator or enquiry route to discuss model, city, eligibility, tenure, EMI, and lender or scheme availability. Final terms and approval remain subject to the applicable financing workflow.
              </p>
            ),
          },
          {
            title: "Monitor, maintain, and get support",
            body: (
              <p>
                Ask the team which monitoring, alerts, installation, pairing, warranty, replacement, and service-routing details apply to your battery and location. Product capabilities and support coverage will be confirmed before commitment.
              </p>
            ),
          },
          {
            title: "What happens after you enquire",
            body: (
              <p>
                The team can confirm the documentation, assessment, installation or activation steps, and service handoff for your case. Include your role and city when you contact iTarang.
              </p>
            ),
          },
          {
            title: "Questions drivers commonly ask",
            body: (
              <ul className="list-disc space-y-2 pl-5">
                <li>Which battery is compatible with my e-rickshaw?</li>
                <li>What purchase or EMI options are available in my city?</li>
                <li>How do charging, service, warranty, and replacement work?</li>
              </ul>
            ),
          },
          {
            title: "A clear next step",
            body: (
              <p>
                Bring your vehicle model, current battery details, city, and financing question to the existing calculator or contact route. iTarang will confirm the appropriate path rather than assume availability or terms.
              </p>
            ),
          },
        ],
        primaryCta: "Check battery and financing options",
        primaryHref: "/how-it-works",
        secondaryCta: "Talk to iTarang",
        secondaryHref: "/contact?role=driver",
      }}
    />
  );
}
