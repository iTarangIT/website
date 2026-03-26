import type { Metadata } from "next";
import { createMetadata } from "@/lib/metadata";
import SectionHeading from "@/components/shared/SectionHeading";
import FadeInOnScroll from "@/components/shared/FadeInOnScroll";
import CTASection from "@/components/shared/CTASection";
import FounderCard from "@/components/about/FounderCard";
import HiringPlan from "@/components/about/HiringPlan";
import AdvisoryBoard from "@/components/about/AdvisoryBoard";
import CompanyDetails from "@/components/about/CompanyDetails";
import FounderVideoPlaceholder from "@/components/about/FounderVideoPlaceholder";

export const metadata: Metadata = createMetadata({
  title: "About",
  description:
    "Meet the iTarang team building India's first EV battery financing and lifecycle management platform. Our mission, founders, and vision for the future.",
  path: "/about",
});

export default function AboutPage() {
  return (
    <>
      {/* Hero */}
      <section className="relative overflow-hidden bg-brand-900 py-24 md:py-32">
        <div
          className="absolute inset-0 opacity-10"
          style={{
            backgroundImage:
              "radial-gradient(circle at 1px 1px, rgba(255,255,255,0.3) 1px, transparent 0)",
            backgroundSize: "32px 32px",
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-br from-brand-900 via-brand-900 to-brand-800" />

        <div className="relative mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 text-center">
          <FadeInOnScroll>
            <SectionHeading
              badge="Our Story"
              title="About iTarang"
              subtitle="We are building the intelligence layer for India's EV battery economy -- making batteries bankable, trackable, and sustainable."
              dark
            />
          </FadeInOnScroll>
        </div>
      </section>

      {/* Company Story */}
      <section className="py-20 md:py-28 bg-white">
        <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
          <FadeInOnScroll>
            <SectionHeading
              badge="Why We Exist"
              title="The Problem We Saw"
            />
          </FadeInOnScroll>

          <FadeInOnScroll delay={0.15}>
            <div className="prose prose-lg mx-auto text-gray-600 max-w-3xl text-center space-y-5">
              <p>
                India&apos;s electric three-wheeler revolution is real -- over 1.2 million
                new vehicles expected by FY27, with 30 lakh already on the road.
                But behind this growth lies a hidden crisis: <strong className="text-gray-900">90% of EV battery
                financing happens informally</strong>, at predatory interest rates of
                30--60%.
              </p>
              <p>
                Drivers and fleet operators -- the backbone of India&apos;s last-mile
                economy -- are trapped in cycles of expensive, unregulated debt
                for their most critical asset. NBFCs want to lend, but without
                real-time battery health data, they cannot underwrite the risk.
              </p>
              <p>
                <strong className="text-gray-900">iTarang bridges this gap.</strong> We
                combine IoT telemetry, behavioral risk scoring, and lifecycle
                management to turn every EV battery into a programmable financial
                asset -- enabling formal credit, reducing NPAs, and unlocking a
                sustainable battery economy from first charge to second life.
              </p>
            </div>
          </FadeInOnScroll>
        </div>
      </section>

      {/* Founder Video Placeholder */}
      <section className="py-16 md:py-20 bg-gray-50">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <FounderVideoPlaceholder />
        </div>
      </section>

      {/* Founders */}
      <section className="py-20 md:py-28 bg-white">
        <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
          <FadeInOnScroll>
            <SectionHeading
              badge="Leadership"
              title="Meet Our Founders"
              subtitle="The driving force behind iTarang's mission to formalize EV battery financing in India."
            />
          </FadeInOnScroll>

          <FounderCard />
        </div>
      </section>

      {/* Hiring */}
      <section className="py-20 md:py-28 bg-gray-50">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <FadeInOnScroll>
            <SectionHeading
              badge="Join Us"
              title="We're Hiring"
              subtitle="Building a world-class team to execute on our vision. These are the roles we are actively looking to fill."
            />
          </FadeInOnScroll>

          <HiringPlan />
        </div>
      </section>

      {/* Advisory Board */}
      <section className="py-20 md:py-28 bg-white">
        <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
          <FadeInOnScroll>
            <SectionHeading
              badge="Advisors"
              title="Advisory Board"
              subtitle="Industry leaders guiding iTarang's strategy across lending, EV markets, and growth."
            />
          </FadeInOnScroll>

          <AdvisoryBoard />
        </div>
      </section>

      {/* Company Details */}
      <section className="py-20 md:py-28 bg-gray-50">
        <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
          <FadeInOnScroll>
            <SectionHeading
              badge="Company Info"
              title="Company Details"
            />
          </FadeInOnScroll>

          <CompanyDetails />
        </div>
      </section>

      {/* CTA */}
      <CTASection
        title="Want to Work With Us?"
        subtitle="Whether you're a potential partner, investor, or future team member -- we'd love to hear from you."
        primaryCTA={{ label: "Get in Touch", href: "/contact" }}
        secondaryCTA={{ label: "View Open Roles", href: "/about#hiring" }}
      />
    </>
  );
}
