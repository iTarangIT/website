"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Battery,
  Globe,
  Mail,
  Phone,
  MessageCircle,
  MapPin,
  ArrowRight,
} from "lucide-react";
import { siteConfig } from "@/data/site";
import Input from "@/components/ui/Input";
import Button from "@/components/ui/Button";

const solutionLinks = [
  { label: "Platform Overview", href: "/solutions" },
  { label: "For NBFCs", href: "/for-nbfcs" },
  { label: "For Investors", href: "/for-investors" },
  { label: "Products", href: "/products" },
];

const companyLinks = [
  { label: "About Us", href: "/about" },
  { label: "Roadmap", href: "/roadmap" },
  { label: "Regulatory", href: "/regulatory" },
  { label: "Competitive Edge", href: "/competitive" },
  { label: "Blog", href: "/blog" },
  { label: "Contact", href: "/contact" },
];

const legalLinks = [
  { label: "Privacy Policy", href: "/privacy" },
  { label: "Terms of Service", href: "/terms" },
  { label: "Cookie Policy", href: "/cookies" },
];

const socialLinks = [
  { icon: Globe, href: siteConfig.social.facebook, label: "Facebook" },
  { icon: Globe, href: siteConfig.social.instagram, label: "Instagram" },
  { icon: Globe, href: siteConfig.social.twitter, label: "Twitter" },
  { icon: Globe, href: siteConfig.social.linkedin, label: "LinkedIn" },
];

export default function Footer() {
  const [email, setEmail] = useState("");
  const [subscribed, setSubscribed] = useState(false);

  const handleNewsletterSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;
    setSubscribed(true);
    setEmail("");
  };

  return (
    <footer className="bg-brand-900 text-white">
      {/* Main Footer */}
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-12">
          {/* Column 1: Brand */}
          <div className="lg:col-span-1">
            <Link href="/" className="flex items-center gap-2 mb-4">
              <Battery className="h-7 w-7 text-brand-300" />
              <span className="text-xl font-bold text-white">iTarang</span>
            </Link>
            <p className="text-brand-200 text-sm leading-relaxed mb-6">
              {siteConfig.tagline}
            </p>
            <div className="flex items-center gap-3">
              {socialLinks.map((social) => (
                <a
                  key={social.label}
                  href={social.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  aria-label={social.label}
                  className="flex h-10 w-10 items-center justify-center rounded-full bg-brand-800 text-brand-300 hover:bg-brand-700 hover:text-white transition-colors"
                >
                  <social.icon className="h-4 w-4" />
                </a>
              ))}
            </div>
          </div>

          {/* Column 2: Solutions */}
          <div>
            <h3 className="text-sm font-semibold uppercase tracking-wider text-brand-300 mb-4">
              Solutions
            </h3>
            <ul className="space-y-3">
              {solutionLinks.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-sm text-brand-200 hover:text-white transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Column 3: Company */}
          <div>
            <h3 className="text-sm font-semibold uppercase tracking-wider text-brand-300 mb-4">
              Company
            </h3>
            <ul className="space-y-3">
              {companyLinks.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-sm text-brand-200 hover:text-white transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Column 4: Contact */}
          <div>
            <h3 className="text-sm font-semibold uppercase tracking-wider text-brand-300 mb-4">
              Contact
            </h3>
            <ul className="space-y-4">
              <li>
                <a
                  href={`mailto:${siteConfig.email}`}
                  className="flex items-center gap-3 text-sm text-brand-200 hover:text-white transition-colors"
                >
                  <Mail className="h-4 w-4 shrink-0" />
                  {siteConfig.email}
                </a>
              </li>
              <li>
                <a
                  href={`tel:${siteConfig.phone}`}
                  className="flex items-center gap-3 text-sm text-brand-200 hover:text-white transition-colors"
                >
                  <Phone className="h-4 w-4 shrink-0" />
                  {siteConfig.phone}
                </a>
              </li>
              <li>
                <a
                  href={`https://wa.me/${siteConfig.whatsapp.replace(/[^0-9]/g, "")}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-3 text-sm text-brand-200 hover:text-white transition-colors"
                >
                  <MessageCircle className="h-4 w-4 shrink-0" />
                  WhatsApp: {siteConfig.whatsapp}
                </a>
              </li>
              <li className="flex items-start gap-3 text-sm text-brand-200">
                <MapPin className="h-4 w-4 shrink-0 mt-0.5" />
                {siteConfig.address}
              </li>
            </ul>
          </div>
        </div>

        {/* Newsletter */}
        <div className="mt-12 pt-8 border-t border-brand-800">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
            <div>
              <h3 className="text-base font-semibold text-white mb-1">
                Subscribe to our newsletter
              </h3>
              <p className="text-sm text-brand-300">
                Get the latest updates on EV battery technology and industry
                insights.
              </p>
            </div>
            {subscribed ? (
              <p className="text-accent-green text-sm font-medium">
                Thank you for subscribing!
              </p>
            ) : (
              <form
                onSubmit={handleNewsletterSubmit}
                className="flex w-full sm:w-auto gap-2"
              >
                <Input
                  type="email"
                  placeholder="Enter your email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="bg-brand-800 border-brand-700 text-white placeholder:text-brand-400 focus:border-brand-400 w-full sm:w-64"
                />
                <Button type="submit" size="md" className="shrink-0">
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </form>
            )}
          </div>
        </div>
      </div>

      {/* Bottom Bar */}
      <div className="border-t border-brand-800">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <p className="text-sm text-brand-400">
              &copy; {new Date().getFullYear()} {siteConfig.name}. All rights
              reserved.
            </p>
            <div className="flex items-center gap-6">
              {legalLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className="text-sm text-brand-400 hover:text-brand-200 transition-colors"
                >
                  {link.label}
                </Link>
              ))}
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
