import { MessageCircle, Truck, Handshake, TrendingUp } from "lucide-react";
import { siteConfig } from "@/data/site";

const deeplinks = [
  {
    label: "I'm a driver/owner interested in battery financing",
    description: "Get details on battery EMI plans and eligibility",
    icon: Truck,
    color: "bg-green-50 border-green-200 hover:bg-green-100",
    iconColor: "text-green-600",
    message: "Hi, I'm a driver/owner interested in battery financing through iTarang. Can you share details?",
  },
  {
    label: "I'm a dealer interested in partnership",
    description: "Learn about iTarang's dealer partner program",
    icon: Handshake,
    color: "bg-brand-50 border-brand-200 hover:bg-brand-100",
    iconColor: "text-brand-600",
    message: "Hi, I'm a dealer interested in partnering with iTarang. Can we discuss the dealer program?",
  },
  {
    label: "I'm an investor/NBFC looking to connect",
    description: "Explore investment and lending partnership opportunities",
    icon: TrendingUp,
    color: "bg-pink-50 border-pink-200 hover:bg-pink-100",
    iconColor: "text-accent-sky",
    message: "Hi, I'm interested in exploring investment/NBFC partnership opportunities with iTarang.",
  },
];

export default function WhatsAppDeeplinks() {
  const phone = siteConfig.whatsapp.replace(/[^0-9]/g, "");

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
        <MessageCircle className="h-4 w-4 text-green-600" />
        Quick WhatsApp Connect
      </h3>
      {deeplinks.map((link) => {
        const Icon = link.icon;
        const url = `https://wa.me/${phone}?text=${encodeURIComponent(link.message)}`;
        return (
          <a
            key={link.label}
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className={`flex items-start gap-3 rounded-xl border p-4 transition-colors ${link.color}`}
          >
            <Icon className={`h-5 w-5 mt-0.5 flex-shrink-0 ${link.iconColor}`} />
            <div>
              <p className="text-sm font-medium text-gray-900">{link.label}</p>
              <p className="text-xs text-gray-500 mt-0.5">{link.description}</p>
            </div>
          </a>
        );
      })}
    </div>
  );
}
