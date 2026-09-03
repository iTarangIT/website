"use client";

import { useState } from "react";
import { CheckCircle, Send } from "lucide-react";
import Input from "@/components/ui/Input";
import Textarea from "@/components/ui/Textarea";
import Button from "@/components/ui/Button";
import { EVENTS, trackEvent } from "@/lib/analytics";

interface FormData {
  name: string;
  email: string;
  phone: string;
  role: string;
  city: string;
  fleetSize: string;
  message: string;
}

const initialData: FormData = {
  name: "",
  email: "",
  phone: "",
  role: "",
  city: "",
  fleetSize: "",
  message: "",
};

export default function ContactForm() {
  const [formData, setFormData] = useState<FormData>(initialData);
  const [errors, setErrors] = useState<Partial<Record<keyof FormData, string>>>({});
  const [submitted, setSubmitted] = useState(false);

  const validate = (): boolean => {
    const newErrors: Partial<Record<keyof FormData, string>> = {};
    if (!formData.name.trim()) newErrors.name = "Name is required";
    if (!formData.email.trim()) {
      newErrors.email = "Email is required";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = "Please enter a valid email";
    }
    if (!formData.role) newErrors.role = "Please select your role";
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    try {
      const existing = JSON.parse(localStorage.getItem("itarang_contact_submissions") || "[]");
      existing.push({ ...formData, submittedAt: new Date().toISOString() });
      localStorage.setItem("itarang_contact_submissions", JSON.stringify(existing));
    } catch {
      // localStorage may not be available
    }

    // The form writes to localStorage and nothing else -- there is no API route
    // behind it and no email is sent, while the success screen promises a reply
    // within 24 hours. That is a separate bug, but until it is fixed this event
    // is the only signal anyone anywhere gets that someone tried to make contact.
    trackEvent(EVENTS.contactSubmit, { role: formData.role || undefined });

    setSubmitted(true);
  };

  const handleChange = (field: keyof FormData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) setErrors((prev) => ({ ...prev, [field]: undefined }));
  };

  if (submitted) {
    return (
      <div className="rounded-2xl border border-gray-200 bg-white p-8 text-center shadow-sm">
        <CheckCircle className="mx-auto h-12 w-12 text-accent-green mb-4" />
        <h3 className="text-xl font-semibold text-gray-900 mb-2">Message Sent!</h3>
        <p className="text-gray-600">Thank you for reaching out. Our team will get back to you within 24 hours.</p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label htmlFor="contact-name" className="block text-sm font-medium text-gray-700 mb-1">
            Full Name *
          </label>
          <Input
            id="contact-name"
            type="text"
            placeholder="Your full name"
            value={formData.name}
            onChange={(e) => handleChange("name", e.target.value)}
          />
          {errors.name && <p className="mt-1 text-xs text-red-500">{errors.name}</p>}
        </div>
        <div>
          <label htmlFor="contact-email" className="block text-sm font-medium text-gray-700 mb-1">
            Email *
          </label>
          <Input
            id="contact-email"
            type="email"
            placeholder="you@example.com"
            value={formData.email}
            onChange={(e) => handleChange("email", e.target.value)}
          />
          {errors.email && <p className="mt-1 text-xs text-red-500">{errors.email}</p>}
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label htmlFor="contact-phone" className="block text-sm font-medium text-gray-700 mb-1">
            Phone
          </label>
          <Input
            id="contact-phone"
            type="tel"
            placeholder="+91 XXXXX XXXXX"
            value={formData.phone}
            onChange={(e) => handleChange("phone", e.target.value)}
          />
        </div>
        <div>
          <label htmlFor="contact-role" className="block text-sm font-medium text-gray-700 mb-1">
            I am a *
          </label>
          <select
            id="contact-role"
            value={formData.role}
            onChange={(e) => handleChange("role", e.target.value)}
            className="w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-sm text-gray-900 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 transition-colors"
          >
            <option value="">Select your role</option>
            <option value="Driver">Driver / Owner</option>
            <option value="Dealer">Dealer</option>
            <option value="NBFC">NBFC Partner</option>
            <option value="Investor">Investor</option>
            <option value="OEM">OEM</option>
            <option value="Other">Other</option>
          </select>
          {errors.role && <p className="mt-1 text-xs text-red-500">{errors.role}</p>}
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label htmlFor="contact-city" className="block text-sm font-medium text-gray-700 mb-1">
            City
          </label>
          <Input
            id="contact-city"
            type="text"
            placeholder="Your city"
            value={formData.city}
            onChange={(e) => handleChange("city", e.target.value)}
          />
        </div>
        <div>
          <label htmlFor="contact-fleet" className="block text-sm font-medium text-gray-700 mb-1">
            Fleet Size
          </label>
          <select
            id="contact-fleet"
            value={formData.fleetSize}
            onChange={(e) => handleChange("fleetSize", e.target.value)}
            className="w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-sm text-gray-900 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 transition-colors"
          >
            <option value="">Select fleet size</option>
            <option value="1-5">1-5 vehicles</option>
            <option value="6-20">6-20 vehicles</option>
            <option value="21-50">21-50 vehicles</option>
            <option value="50+">50+ vehicles</option>
            <option value="N/A">Not Applicable</option>
          </select>
        </div>
      </div>

      <div>
        <label htmlFor="contact-message" className="block text-sm font-medium text-gray-700 mb-1">
          Message
        </label>
        <Textarea
          id="contact-message"
          placeholder="Tell us how we can help..."
          rows={4}
          value={formData.message}
          onChange={(e) => handleChange("message", e.target.value)}
        />
      </div>

      <Button type="submit" size="md" className="w-full">
        <Send className="h-4 w-4 mr-2" />
        Send Message
      </Button>
    </form>
  );
}
