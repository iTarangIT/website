"use client";

import { useState } from "react";
import { LogIn } from "lucide-react";
import { cn } from "@/lib/utils";
import LoginModal from "./LoginModal";

interface LoginButtonProps {
  scrolled?: boolean;
  fullWidth?: boolean;
  variant?: "navbar" | "mobile";
  onClick?: () => void;
}

export default function LoginButton({ scrolled = true, fullWidth = false, variant = "navbar", onClick }: LoginButtonProps) {
  const [open, setOpen] = useState(false);

  const handleOpen = () => {
    onClick?.();
    setOpen(true);
  };

  if (variant === "mobile") {
    return (
      <>
        <button
          onClick={handleOpen}
          className={cn(
            "flex items-center justify-center gap-2 px-4 py-3 text-base font-semibold rounded-xl transition-colors font-sans",
            "bg-brand-50 text-brand-700 hover:bg-brand-100",
            fullWidth && "w-full",
          )}
        >
          <LogIn className="h-4 w-4" />
          Log in
        </button>
        <LoginModal open={open} onOpenChange={setOpen} />
      </>
    );
  }

  return (
    <>
      <button
        onClick={handleOpen}
        className={cn(
          "inline-flex items-center gap-1.5 px-4 py-2 text-sm font-semibold rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-brand-400 focus:ring-offset-2",
          scrolled
            ? "border-2 border-brand-500 text-brand-500 hover:bg-brand-50"
            : "border-2 border-white/30 text-white hover:bg-white/10",
        )}
      >
        <LogIn className="h-3.5 w-3.5" />
        Log in
      </button>
      <LoginModal open={open} onOpenChange={setOpen} />
    </>
  );
}
