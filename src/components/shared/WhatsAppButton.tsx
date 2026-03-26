"use client";

import { MessageCircle } from "lucide-react";
import { motion } from "framer-motion";
import { siteConfig } from "@/data/site";

export default function WhatsAppButton() {
  const phoneNumber = siteConfig.whatsapp.replace(/[^0-9]/g, "");
  const url = `https://wa.me/${phoneNumber}?text=${encodeURIComponent(
    "Hi, I'd like to learn more about iTarang's EV battery financing solutions."
  )}`;

  return (
    <motion.a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      aria-label="Chat on WhatsApp"
      initial={{ scale: 0, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{
        type: "spring",
        stiffness: 260,
        damping: 20,
        delay: 1,
      }}
      whileHover={{ scale: 1.1 }}
      whileTap={{ scale: 0.95 }}
      className="fixed bottom-6 right-6 z-50 flex h-14 w-14 items-center justify-center rounded-full bg-green-500 text-white shadow-lg hover:shadow-xl focus:outline-none focus:ring-2 focus:ring-green-400 focus:ring-offset-2"
    >
      <MessageCircle className="h-6 w-6" />
    </motion.a>
  );
}
