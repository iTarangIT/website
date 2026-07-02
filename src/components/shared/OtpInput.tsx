"use client";

import { useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface OtpInputProps {
  length?: number;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  error?: boolean;
}

export default function OtpInput({
  length = 6,
  value,
  onChange,
  disabled = false,
  error = false,
}: OtpInputProps) {
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  useEffect(() => {
    inputRefs.current[0]?.focus();
  }, []);

  // Refocus the first box after a failed attempt clears the value
  useEffect(() => {
    if (error && value.length === 0) {
      inputRefs.current[0]?.focus();
    }
  }, [error, value]);

  const setDigits = (digits: string, focusIndex: number) => {
    onChange(digits.slice(0, length));
    const target = Math.min(focusIndex, length - 1);
    inputRefs.current[target]?.focus();
  };

  const handleChange = (index: number, raw: string) => {
    const digits = raw.replace(/\D/g, "");
    if (!digits) return;

    if (digits.length > 1) {
      // Paste or mobile keyboard autofill landing in a single box
      const next = (value.slice(0, index) + digits).slice(0, length);
      setDigits(next, next.length);
      return;
    }

    const next = (value.slice(0, index) + digits + value.slice(index + 1)).slice(0, length);
    setDigits(next, index + 1);
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Backspace") {
      e.preventDefault();
      if (value[index]) {
        onChange(value.slice(0, index) + value.slice(index + 1));
      } else if (index > 0) {
        onChange(value.slice(0, index - 1) + value.slice(index));
        inputRefs.current[index - 1]?.focus();
      }
      return;
    }
    if (e.key === "ArrowLeft" && index > 0) {
      e.preventDefault();
      inputRefs.current[index - 1]?.focus();
      return;
    }
    if (e.key === "ArrowRight" && index < length - 1) {
      e.preventDefault();
      inputRefs.current[index + 1]?.focus();
      return;
    }
    if (e.key.length === 1 && !/\d/.test(e.key) && !e.ctrlKey && !e.metaKey) {
      e.preventDefault();
    }
  };

  const handlePaste = (e: React.ClipboardEvent<HTMLDivElement>) => {
    e.preventDefault();
    const digits = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, length);
    if (digits) setDigits(digits, digits.length);
  };

  return (
    <motion.div
      className="flex justify-center gap-2 sm:gap-3"
      animate={error ? { x: [0, -6, 6, -4, 4, 0] } : { x: 0 }}
      transition={{ duration: 0.3 }}
      onPaste={handlePaste}
    >
      {Array.from({ length }, (_, i) => (
        <input
          key={i}
          ref={(el) => {
            inputRefs.current[i] = el;
          }}
          type="text"
          inputMode="numeric"
          pattern="[0-9]*"
          maxLength={length}
          autoComplete={i === 0 ? "one-time-code" : "off"}
          aria-label={`Digit ${i + 1}`}
          aria-invalid={error}
          disabled={disabled}
          value={value[i] ?? ""}
          onChange={(e) => handleChange(i, e.target.value)}
          onKeyDown={(e) => handleKeyDown(i, e)}
          onFocus={(e) => e.target.select()}
          className={cn(
            "h-12 w-10 sm:w-12 rounded-lg border bg-white text-center text-lg font-semibold text-gray-900 focus:outline-none focus:ring-2 transition-colors disabled:opacity-50",
            error
              ? "border-red-400 focus:border-red-400 focus:ring-red-400/20"
              : "border-gray-300 focus:border-brand-500 focus:ring-brand-500/20"
          )}
        />
      ))}
    </motion.div>
  );
}
