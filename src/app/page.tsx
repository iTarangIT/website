import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";
import WhatsAppButton from "@/components/shared/WhatsAppButton";
import TrustBadgeStrip from "@/components/shared/TrustBadgeStrip";
import CTASection from "@/components/shared/CTASection";
import HeroSection from "@/components/home/HeroSection";
import ProblemSection from "@/components/home/ProblemSection";
import SolutionOverview from "@/components/home/SolutionOverview";
import TractionSection from "@/components/home/TractionSection";
import DataFlywheelPreview from "@/components/home/DataFlywheelPreview";
import AudienceCTASection from "@/components/home/AudienceCTASection";

export default function Home() {
  return (
    <>
      <Navbar />

      <main className="flex-1">
        <HeroSection />
        <TrustBadgeStrip />
        <ProblemSection />
        <SolutionOverview />
        <DataFlywheelPreview />
        <TractionSection />
        <AudienceCTASection />
        <CTASection
          title="Ready to Transform EV Battery Financing?"
          subtitle="Join the ecosystem that's making batteries bankable."
          primaryCTA={{ label: "Schedule a Call", href: "/contact" }}
          secondaryCTA={{ label: "Request Pitch Deck", href: "/for-investors" }}
        />
      </main>

      <Footer />
      <WhatsAppButton />
    </>
  );
}
