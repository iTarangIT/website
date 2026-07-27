import AudienceLandingPage from "@/components/partners/AudienceLandingPage";
import { createMetadata } from "@/lib/metadata";

export const metadata = createMetadata({
  title: "E-Rickshaw Battery Lifecycle, Monitoring and EPR for OEMs — iTarang",
  description:
    "Explore iTarang battery lifecycle, monitoring, recovery, recycling, and EPR collaboration options for e-rickshaw OEMs in India.",
  path: "/for-oems",
});

export default function ForOemsPage() {
  return (
    <AudienceLandingPage
      page={{
        eyebrow: "For OEMs",
        title: "E-Rickshaw Battery Lifecycle Solutions for OEMs",
        intro:
          "Discuss design-in, deployment, monitoring, recovery, recycling, and EPR requirements with iTarang. We will separate currently available capabilities from integration or roadmap discussions.",
        sections: [
          {
            title: "Design-in and deployment collaboration",
            body: (
              <p>
                Begin with your vehicle, battery, compatibility, installation, telemetry, and technical-review requirements. Integration scope, data ownership, security, and responsibilities should be agreed before a pilot or deployment is proposed.
              </p>
            ),
          },
          {
            title: "Monitor battery health across the lifecycle",
            body: (
              <p>
                Ask which state-of-health, state-of-charge, location, temperature, charge-cycle, and alert data are available for your use case. The team will distinguish current product features from planned capabilities.
              </p>
            ),
          },
          {
            title: "Maintain, recover, and recycle",
            body: (
              <p>
                Discuss service, recovery, second-life, recycling, and chain-of-custody requirements with the lifecycle team. Any recovery rate, buyback term, environmental outcome, or geographic coverage must be confirmed for your program.
              </p>
            ),
          },
          {
            title: "EPR and battery-passport readiness",
            body: (
              <p>
                Share the jurisdictions, dates, registration, reporting, recycling, and documentation requirements that apply to your organization. iTarang can discuss data and workflow support; using the service alone does not constitute legal compliance.
              </p>
            ),
          },
          {
            title: "Pilot and integration questions",
            body: (
              <ul className="list-disc space-y-2 pl-5">
                <li>Which API, LOS, LMS, telemetry, or lifecycle integration scope is required?</li>
                <li>What pilot criteria, implementation responsibilities, and timeline should be reviewed?</li>
                <li>How will data access, ownership, security, and reporting be handled?</li>
              </ul>
            ),
          },
          {
            title: "Discuss an OEM requirement",
            body: (
              <p>
                Include your organization, fleet or vehicle context, geography, and lifecycle or EPR question in the enquiry. The product and legal stakeholders can then confirm a responsible next step.
              </p>
            ),
          },
        ],
        primaryCta: "Discuss an OEM requirement",
        primaryHref: "/contact?role=oem",
        secondaryCta: "View partner overview",
        secondaryHref: "/for-partners",
      }}
    />
  );
}
