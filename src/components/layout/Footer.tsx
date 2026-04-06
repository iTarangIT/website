"use client";

import Link from "next/link";
import { Battery, Mail, Phone, MessageCircle } from "lucide-react";
import { siteConfig } from "@/data/site";

const siteLinks = [
  { label: "How It Works", href: "/how-it-works" },
  { label: "For Partners", href: "/for-partners" },
  { label: "About", href: "/about" },
  { label: "Contact", href: "/contact" },
];

const moreLinks = [
  { label: "Blog", href: "/blog" },
  { label: "For Investors", href: "/for-investors" },
];

const socialLinks = [
  { href: siteConfig.social.linkedin, label: "LinkedIn" },
  { href: siteConfig.social.twitter, label: "Twitter" },
  { href: siteConfig.social.instagram, label: "Instagram" },
];

export default function Footer() {
  return (
    <footer className="relative overflow-hidden">
      {/* Main footer area */}
      <div className="bg-gradient-to-b from-brand-950 to-[#030d33] pt-20 pb-12">
        {/* Ambient glow */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-[radial-gradient(ellipse,rgba(5,27,154,0.15),transparent_70%)] pointer-events-none" />

        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-12">
            {/* Brand */}
            <div className="lg:col-span-1">
              <Link href="/" className="flex items-center gap-2.5 mb-5">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-400 to-brand-600 flex items-center justify-center">
                  <Battery className="h-4 w-4 text-white" />
                </div>
                <span className="text-lg font-bold text-white font-sans">iTarang</span>
              </Link>
              <p className="text-brand-300/50 text-sm leading-relaxed mb-6 max-w-xs font-sans">
                {siteConfig.tagline}
              </p>
              <div className="flex items-center gap-4">
                {socialLinks.map((social) => (
                  <a
                    key={social.label}
                    href={social.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-brand-300/40 hover:text-brand-300 transition-colors font-sans uppercase tracking-widest"
                  >
                    {social.label}
                  </a>
                ))}
              </div>
            </div>

            {/* Site Links */}
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-300/40 mb-5 font-sans">
                Site
              </h3>
              <ul className="space-y-3">
                {siteLinks.map((link) => (
                  <li key={link.href}>
                    <Link
                      href={link.href}
                      className="text-sm text-brand-200/60 hover:text-white transition-colors font-sans"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>

            {/* More */}
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-300/40 mb-5 font-sans">
                More
              </h3>
              <ul className="space-y-3">
                {moreLinks.map((link) => (
                  <li key={link.href}>
                    <Link
                      href={link.href}
                      className="text-sm text-brand-200/60 hover:text-white transition-colors font-sans"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>

            {/* Contact */}
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-300/40 mb-5 font-sans">
                Contact
              </h3>
              <ul className="space-y-4">
                <li>
                  <a href={`mailto:${siteConfig.email}`} className="flex items-center gap-3 text-sm text-brand-200/60 hover:text-white transition-colors font-sans">
                    <Mail className="h-3.5 w-3.5 shrink-0" />
                    {siteConfig.email}
                  </a>
                </li>
                <li>
                  <a href={`tel:${siteConfig.phone}`} className="flex items-center gap-3 text-sm text-brand-200/60 hover:text-white transition-colors font-sans">
                    <Phone className="h-3.5 w-3.5 shrink-0" />
                    {siteConfig.phone}
                  </a>
                </li>
                <li>
                  <a
                    href={`https://wa.me/${siteConfig.whatsapp.replace(/[^0-9]/g, "")}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-3 text-sm text-brand-200/60 hover:text-white transition-colors font-sans"
                  >
                    <MessageCircle className="h-3.5 w-3.5 shrink-0" />
                    WhatsApp
                  </a>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom bar */}
      <div className="bg-[#030d33] border-t border-brand-800/30">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-5">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <p className="text-xs text-brand-400/30 font-sans">
              &copy; {new Date().getFullYear()} {siteConfig.name}. All rights reserved.
            </p>
            <div className="flex items-center gap-6">
              <Link href="/privacy" className="text-xs text-brand-400/30 hover:text-brand-300/60 transition-colors font-sans">
                Privacy Policy
              </Link>
              <Link href="/terms" className="text-xs text-brand-400/30 hover:text-brand-300/60 transition-colors font-sans">
                Terms of Service
              </Link>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
