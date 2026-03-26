"use client";

import { useState } from "react";
import { CheckCircle, Download } from "lucide-react";
import Input from "@/components/ui/Input";
import Select from "@/components/ui/Select";
import Button from "@/components/ui/Button";

interface GatedFormData {
  name: string;
  company: string;
  email: string;
  role: string;
}

interface GatedFormProps {
  title: string;
  description: string;
  onSubmit?: (data: GatedFormData) => void;
  downloadUrl?: string;
}

const STORAGE_KEY = "itarang_gated_submissions";

export default function GatedForm({
  title,
  description,
  onSubmit,
  downloadUrl,
}: GatedFormProps) {
  const [formData, setFormData] = useState<GatedFormData>({
    name: "",
    company: "",
    email: "",
    role: "",
  });
  const [submitted, setSubmitted] = useState(false);
  const [errors, setErrors] = useState<Partial<Record<keyof GatedFormData, string>>>({});

  const validate = (): boolean => {
    const newErrors: Partial<Record<keyof GatedFormData, string>> = {};

    if (!formData.name.trim()) newErrors.name = "Name is required";
    if (!formData.company.trim()) newErrors.company = "Company/Fund is required";
    if (!formData.email.trim()) {
      newErrors.email = "Email is required";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = "Please enter a valid email";
    }
    if (!formData.role) newErrors.role = "Please select a role";

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) return;

    // Store to localStorage
    try {
      const existing = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
      existing.push({ ...formData, submittedAt: new Date().toISOString() });
      localStorage.setItem(STORAGE_KEY, JSON.stringify(existing));
    } catch {
      // localStorage may not be available
    }

    // Call optional onSubmit callback
    onSubmit?.(formData);

    // Trigger download if URL is provided
    if (downloadUrl) {
      const link = document.createElement("a");
      link.href = downloadUrl;
      link.download = "";
      link.target = "_blank";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }

    setSubmitted(true);
  };

  const handleChange = (field: keyof GatedFormData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: undefined }));
    }
  };

  if (submitted) {
    return (
      <div className="rounded-2xl border border-gray-200 bg-white p-8 text-center shadow-sm">
        <CheckCircle className="mx-auto h-12 w-12 text-accent-green mb-4" />
        <h3 className="text-xl font-semibold text-gray-900 mb-2">
          Thank you!
        </h3>
        <p className="text-gray-600">
          {downloadUrl
            ? "Your download should begin shortly. Check your downloads folder."
            : "We'll be in touch soon."}
        </p>
        {downloadUrl && (
          <a
            href={downloadUrl}
            download
            target="_blank"
            rel="noopener noreferrer"
            className="mt-4 inline-flex items-center gap-2 text-sm font-medium text-brand-600 hover:text-brand-700"
          >
            <Download className="h-4 w-4" />
            Download again
          </a>
        )}
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-8 shadow-sm">
      <h3 className="text-xl font-semibold text-gray-900 mb-1">{title}</h3>
      <p className="text-sm text-gray-600 mb-6">{description}</p>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Name */}
        <div>
          <label
            htmlFor="gated-name"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Name *
          </label>
          <Input
            id="gated-name"
            type="text"
            placeholder="Your full name"
            value={formData.name}
            onChange={(e) => handleChange("name", e.target.value)}
          />
          {errors.name && (
            <p className="mt-1 text-xs text-red-500">{errors.name}</p>
          )}
        </div>

        {/* Company / Fund */}
        <div>
          <label
            htmlFor="gated-company"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Company / Fund *
          </label>
          <Input
            id="gated-company"
            type="text"
            placeholder="Your organization"
            value={formData.company}
            onChange={(e) => handleChange("company", e.target.value)}
          />
          {errors.company && (
            <p className="mt-1 text-xs text-red-500">{errors.company}</p>
          )}
        </div>

        {/* Email */}
        <div>
          <label
            htmlFor="gated-email"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Email *
          </label>
          <Input
            id="gated-email"
            type="email"
            placeholder="you@company.com"
            value={formData.email}
            onChange={(e) => handleChange("email", e.target.value)}
          />
          {errors.email && (
            <p className="mt-1 text-xs text-red-500">{errors.email}</p>
          )}
        </div>

        {/* Role */}
        <div>
          <label
            htmlFor="gated-role"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Role *
          </label>
          <Select
            id="gated-role"
            value={formData.role}
            onChange={(e) => handleChange("role", e.target.value)}
          >
            <option value="">Select your role</option>
            <option value="Investor">Investor</option>
            <option value="NBFC">NBFC</option>
            <option value="Dealer">Dealer</option>
            <option value="OEM">OEM</option>
            <option value="Other">Other</option>
          </Select>
          {errors.role && (
            <p className="mt-1 text-xs text-red-500">{errors.role}</p>
          )}
        </div>

        <Button type="submit" size="md" className="w-full mt-2">
          {downloadUrl ? "Download Now" : "Submit"}
        </Button>
      </form>
    </div>
  );
}
