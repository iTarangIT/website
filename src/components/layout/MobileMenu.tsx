"use client";

import { useState } from "react";
import Link from "next/link";
import { X, ChevronDown, Battery } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { mainNavItems, type NavItem } from "@/data/navigation";
import Button from "@/components/ui/Button";

interface MobileMenuProps {
  isOpen: boolean;
  onClose: () => void;
}

function MobileNavItem({
  item,
  onClose,
}: {
  item: NavItem;
  onClose: () => void;
}) {
  const [expanded, setExpanded] = useState(false);

  if (!item.children) {
    return (
      <Link
        href={item.href}
        onClick={onClose}
        className="block px-6 py-3 text-lg font-medium text-gray-800 hover:text-brand-600 hover:bg-brand-50 transition-colors"
      >
        {item.label}
      </Link>
    );
  }

  return (
    <div>
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center justify-between px-6 py-3 text-lg font-medium text-gray-800 hover:text-brand-600 hover:bg-brand-50 transition-colors"
      >
        {item.label}
        <ChevronDown
          className={cn(
            "h-5 w-5 transition-transform duration-200",
            expanded && "rotate-180"
          )}
        />
      </button>
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="bg-brand-50/50 py-1">
              {item.children.map((child) => (
                <Link
                  key={child.href}
                  href={child.href}
                  onClick={onClose}
                  className="block px-10 py-2.5 text-base text-gray-600 hover:text-brand-600 transition-colors"
                >
                  {child.label}
                </Link>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
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

            {/* Navigation Items */}
            <div className="flex-1 overflow-y-auto py-4">
              {mainNavItems.map((item) => (
                <MobileNavItem
                  key={item.href}
                  item={item}
                  onClose={onClose}
                />
              ))}
            </div>

            {/* CTA */}
            <div className="p-6 border-t border-gray-100">
              <Button href="/contact" size="lg" className="w-full">
                Get Started
              </Button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
