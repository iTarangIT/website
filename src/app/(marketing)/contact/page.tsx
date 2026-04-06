import type { Metadata } from "next";
import { siteConfig } from "@/data/site";
import { Card, CardContent } from "@/components/ui/Card";
import FadeInOnScroll from "@/components/shared/FadeInOnScroll";
import ContactForm from "@/components/contact/ContactForm";
import { Mail, Phone, MapPin, Clock, MessageCircle } from "lucide-react";

export const metadata: Metadata = {
  title: "Contact | iTarang",
  description:
    "Get in touch with iTarang. Whether you're a driver, dealer, NBFC, or investor — we'd love to hear from you.",
};

const contactInfo = [
  { icon: Mail, label: "Email", value: siteConfig.email, href: `mailto:${siteConfig.email}` },
  { icon: Phone, label: "Phone", value: siteConfig.phone, href: `tel:${siteConfig.phone}` },
  { icon: MapPin, label: "Office", value: siteConfig.address },
  { icon: Clock, label: "Hours", value: siteConfig.hours },
];

const whatsappRoles = [
  { label: "I'm a Driver", message: "Hi, I'm a driver interested in iTarang batteries.", emoji: "🛺" },
  { label: "I'm a Dealer", message: "Hi, I'm a dealer interested in partnering with iTarang.", emoji: "🏪" },
  { label: "I'm an NBFC", message: "Hi, I represent an NBFC interested in iTarang's lending platform.", emoji: "🏦" },
  { label: "I'm an Investor", message: "Hi, I'm an investor interested in learning more about iTarang.", emoji: "📊" },
];

export default function ContactPage() {
  const phoneNumber = siteConfig.whatsapp.replace(/[^0-9]/g, "");

  return (
    <>
      {/* Hero */}
      <section className="pt-28 pb-16 md:pt-36 md:pb-20 relative overflow-hidden">
        <div className="absolute inset-0 bg-surface-warm" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_left,rgba(5,27,154,0.06),transparent_60%)]" />
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 relative z-10">
          <span className="inline-block text-sm font-semibold text-brand-500 tracking-widest uppercase mb-4 font-sans">
            Contact
          </span>
          <h1 className="text-5xl md:text-7xl text-gray-900 tracking-tight leading-[1.05]">
            Get in Touch
          </h1>
          <p className="mt-6 text-xl text-gray-500 max-w-2xl leading-relaxed font-sans">
            Whether you&apos;re a driver, dealer, NBFC partner, or investor — we&apos;d
            love to hear from you.
          </p>
        </div>
      </section>

      {/* Contact Section */}
      <section className="py-16 md:py-24 bg-white">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="grid gap-12 lg:grid-cols-5">
            {/* Form */}
            <FadeInOnScroll className="lg:col-span-3">
              <Card className="border-gray-200/60 shadow-xl shadow-gray-900/5">
                <CardContent>
                  <h2 className="text-2xl text-gray-900 mb-6">
                    Send us a message
                  </h2>
                  <ContactForm />
                </CardContent>
              </Card>
            </FadeInOnScroll>

            {/* Sidebar */}
            <FadeInOnScroll delay={0.2} className="lg:col-span-2 space-y-6">
              {/* WhatsApp Quick Connect */}
              <div className="rounded-2xl bg-gradient-to-br from-emerald-50 to-green-50/50 border border-emerald-200/40 p-6">
                <div className="flex items-center gap-2.5 mb-5">
                  <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center">
                    <MessageCircle className="h-4 w-4 text-emerald-600" />
                  </div>
                  <h3 className="text-sm font-semibold text-emerald-800 font-sans">
                    Quick Connect via WhatsApp
                  </h3>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  {whatsappRoles.map((role) => (
                    <a
                      key={role.label}
                      href={`https://wa.me/${phoneNumber}?text=${encodeURIComponent(role.message)}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="rounded-xl bg-white border border-emerald-200/40 px-3 py-3 text-xs font-medium text-emerald-700 hover:bg-emerald-50 hover:border-emerald-300 transition-all text-center font-sans"
                    >
                      <span className="block text-base mb-1">{role.emoji}</span>
                      {role.label}
                    </a>
                  ))}
                </div>
              </div>

              {/* Contact Info */}
              <div className="rounded-2xl bg-surface-warm border border-gray-200/40 p-6 space-y-5">
                <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-[0.2em] font-sans">
                  Contact Info
                </h3>
                {contactInfo.map(({ icon: Icon, label, value, href }) => (
                  <div key={label} className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-lg bg-brand-500/5 flex items-center justify-center shrink-0 mt-0.5">
                      <Icon className="h-3.5 w-3.5 text-brand-500" />
                    </div>
                    <div>
                      <p className="text-[10px] text-gray-400 uppercase tracking-wider font-sans">{label}</p>
                      {href ? (
                        <a href={href} className="text-sm font-medium text-gray-900 hover:text-brand-600 transition-colors font-sans">
                          {value}
                        </a>
                      ) : (
                        <p className="text-sm font-medium text-gray-900 font-sans">{value}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </FadeInOnScroll>
          </div>
        </div>
      </section>
    </>
  );
}
