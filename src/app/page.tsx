import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";
import WhatsAppButton from "@/components/shared/WhatsAppButton";
import HeroSection from "@/components/home/HeroSection";
import LifecycleStrip from "@/components/home/LifecycleStrip";
import ProofStrip from "@/components/home/ProofStrip";
import WhoWeServe from "@/components/home/WhoWeServe";
import SocialProof from "@/components/home/SocialProof";
import HomeCTA from "@/components/home/HomeCTA";
import FloatingDock from "@/components/layout/FloatingDock";

export default function Home() {
  return (
    <>
      <Navbar />

      <main className="flex-1">
        <HeroSection />
        <LifecycleStrip />
        <ProofStrip />
        <WhoWeServe />
        <SocialProof />
        <HomeCTA />
      </main>

      <Footer />
      <FloatingDock />
      <WhatsAppButton />
    </>
  );
}
