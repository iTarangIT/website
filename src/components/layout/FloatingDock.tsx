"use client";

import { Dock } from "@/components/ui/dock-two";
import {
  Zap,
  Handshake,
  Users,
  Mail,
  MessageCircle,
} from "lucide-react";

const dockItems = [
  { icon: Zap, label: "How It Works", href: "/how-it-works" },
  { icon: Handshake, label: "Partners", href: "/for-partners" },
  { icon: Users, label: "About", href: "/about" },
  { icon: Mail, label: "Contact", href: "/contact" },
  { icon: MessageCircle, label: "WhatsApp", href: "https://wa.me/918920828425" },
];

export default function FloatingDock() {
  return (
    <div className="hidden md:block">
      <Dock
        items={dockItems}
        className="backdrop-blur-xl bg-white/80 border-gray-200/50 shadow-lg shadow-gray-900/5"
      />
    </div>
  );
}
