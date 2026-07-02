"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, BarChart3, Store, Users } from "lucide-react";
import { cn } from "@/lib/utils";

type AudienceOption = {
  id: string;
  label: string;
  Icon: typeof BarChart3;
};

const OPTIONS: AudienceOption[] = [
  { id: "nbfc", label: "NBFC", Icon: BarChart3 },
  { id: "dealer", label: "Dealer", Icon: Store },
  { id: "customer", label: "Customer", Icon: Users },
];

export default function AudienceDropdown({ solid = false }: { solid?: boolean }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const router = useRouter();

  useEffect(() => {
    if (!open) return;
    const onDocClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onDocClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDocClick);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  const pick = (id: string) => {
    setOpen(false);
    router.push(`/for-partners#${id}`);
  };

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((o) => !o)}
        aria-haspopup="menu"
        aria-expanded={open}
        className={cn(
          "inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-xl border transition-colors",
          solid
            ? "bg-white hover:bg-brand-50 text-gray-600 hover:text-brand-600 border-gray-200 shadow-sm"
            : "bg-brand-900/70 hover:bg-brand-900/90 text-white/80 hover:text-white border-brand-400/20 backdrop-blur-sm shadow-[0_0_20px_rgba(0,0,0,0.25)]"
        )}
      >
        I am a…
        <motion.span
          animate={{ rotate: open ? 180 : 0 }}
          transition={{ duration: 0.4, ease: "easeInOut", type: "spring" }}
        >
          <ChevronDown className="h-4 w-4" />
        </motion.span>
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            role="menu"
            initial={{ y: -5, scale: 0.95, opacity: 0, filter: "blur(10px)" }}
            animate={{ y: 0, scale: 1, opacity: 1, filter: "blur(0px)" }}
            exit={{ y: -5, scale: 0.95, opacity: 0, filter: "blur(10px)" }}
            transition={{ duration: 0.4, ease: "circInOut", type: "spring" }}
            className={cn(
              "absolute right-0 z-20 mt-2 w-48 p-1 rounded-xl border backdrop-blur-md flex flex-col gap-1",
              solid
                ? "bg-white border-gray-200 shadow-lg"
                : "bg-brand-900/80 border-brand-400/20 shadow-[0_0_20px_rgba(0,0,0,0.3)]"
            )}
          >
            {OPTIONS.map((option, index) => {
              const Icon = option.Icon;
              return (
                <motion.button
                  key={option.id}
                  role="menuitem"
                  initial={{ opacity: 0, x: 10, filter: "blur(10px)" }}
                  animate={{ opacity: 1, x: 0, filter: "blur(0px)" }}
                  transition={{
                    duration: 0.3,
                    delay: index * 0.08,
                    ease: "easeInOut",
                  }}
                  whileHover={{
                    backgroundColor: solid
                      ? "rgba(0,0,0,0.04)"
                      : "rgba(255,255,255,0.06)",
                  }}
                  whileTap={{ scale: 0.97 }}
                  onClick={() => pick(option.id)}
                  className={cn(
                    "px-3 py-2.5 cursor-pointer text-sm rounded-lg w-full text-left flex items-center gap-x-2 transition-colors",
                    solid ? "text-gray-700" : "text-white/80",
                  )}
                >
                  <Icon className={cn("h-4 w-4", solid ? "text-brand-500" : "text-brand-300")} />
                  {option.label}
                </motion.button>
              );
            })}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
