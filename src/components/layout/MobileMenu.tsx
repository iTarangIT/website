"use client";

import Link from "next/link";
import { X, Battery } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { mainNavItems } from "@/data/navigation";
import Button from "@/components/ui/Button";

interface MobileMenuProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function MobileMenu({ isOpen, onClose }: MobileMenuProps) {
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-50 bg-black/40"
            onClick={onClose}
          />

          {/* Panel */}
          <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", damping: 30, stiffness: 300 }}
            className="fixed top-0 right-0 bottom-0 z-50 w-full max-w-sm bg-white shadow-2xl"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
              <Link
                href="/"
                onClick={onClose}
                className="flex items-center gap-2"
              >
                <Battery className="h-6 w-6 text-brand-500" />
                <span className="text-lg font-bold text-brand-500">
                  iTarang
                </span>
              </Link>
              <button
                onClick={onClose}
                className="p-2 text-gray-500 hover:text-gray-800 transition-colors"
                aria-label="Close menu"
              >
                <X className="h-6 w-6" />
              </button>
            </div>

            {/* Flat Navigation */}
            <div className="flex-1 overflow-y-auto py-4">
              {mainNavItems.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={onClose}
                  className="block px-6 py-3 text-lg font-medium text-gray-800 hover:text-brand-600 hover:bg-brand-50 transition-colors"
                >
                  {item.label}
                </Link>
              ))}
              <Link
                href="/for-investors"
                onClick={onClose}
                className="block px-6 py-3 text-lg font-medium text-gray-500 hover:text-brand-600 hover:bg-brand-50 transition-colors"
              >
                For Investors
              </Link>
            </div>

            {/* CTA */}
            <div className="p-6 border-t border-gray-100">
              <Button href="/contact" size="lg" className="w-full">
                Talk to Us
              </Button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
