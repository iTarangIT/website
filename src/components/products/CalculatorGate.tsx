"use client";

import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { CheckCircle, Loader2, Lock, ShieldCheck } from "lucide-react";
import Input from "@/components/ui/Input";
import Button from "@/components/ui/Button";
import OtpInput from "@/components/shared/OtpInput";
import { cn } from "@/lib/utils";
import {
  DEV_OTP_CODE,
  isValidIndianMobile,
  maskPhone,
  normalizePhone,
  sendOtp,
  verifyOtp,
} from "@/lib/otp";

const VERIFIED_KEY = "itarang_calculator_verified";
const LEADS_KEY = "itarang_calculator_leads";

type Step = "loading" | "form" | "otp" | "success" | "unlocked";

interface CalculatorGateProps {
  children: React.ReactNode;
}

export default function CalculatorGate({ children }: CalculatorGateProps) {
  const [step, setStep] = useState<Step>("loading");
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [formErrors, setFormErrors] = useState<{ name?: string; phone?: string }>({});
  const [otp, setOtp] = useState("");
  const [otpError, setOtpError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [resendIn, setResendIn] = useState(0);
  const [mockActive, setMockActive] = useState(false);

  const nameInputRef = useRef<HTMLInputElement>(null);
  const unlockTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Returning-visitor check — localStorage is only touched after mount
  useEffect(() => {
    let verified = false;
    try {
      const stored = JSON.parse(localStorage.getItem(VERIFIED_KEY) || "null");
      verified = Boolean(stored && stored.phone && stored.verifiedAt);
    } catch {
      // corrupt/unavailable storage → treat as unverified
    }
    setStep(verified ? "unlocked" : "form");
  }, []);

  useEffect(() => {
    if (step === "form") nameInputRef.current?.focus();
  }, [step]);

  // Resend countdown
  useEffect(() => {
    if (step !== "otp" || resendIn <= 0) return;
    const t = setTimeout(() => setResendIn((s) => s - 1), 1000);
    return () => clearTimeout(t);
  }, [step, resendIn]);

  useEffect(() => {
    return () => {
      if (unlockTimeoutRef.current) clearTimeout(unlockTimeoutRef.current);
    };
  }, []);

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (busy) return;

    const errors: { name?: string; phone?: string } = {};
    if (name.trim().length < 2) errors.name = "Please enter your name";
    if (!isValidIndianMobile(phone)) {
      errors.phone = "Enter a valid 10-digit Indian mobile number";
    }
    setFormErrors(errors);
    if (Object.keys(errors).length > 0) return;

    setBusy(true);
    const result = await sendOtp(normalizePhone(phone));
    setBusy(false);
    if (result.success) {
      setMockActive(Boolean(result.mock));
      setOtp("");
      setOtpError(null);
      setResendIn(30);
      setStep("otp");
    } else {
      setFormErrors({ phone: result.error || "Could not send OTP. Please try again." });
    }
  };

  const handleVerify = async (code: string) => {
    if (busy || code.length !== 6) return;
    setBusy(true);
    const result = await verifyOtp(code);
    if (result.success) {
      const lead = {
        name: name.trim(),
        phone: normalizePhone(phone),
        verifiedAt: new Date().toISOString(),
      };
      try {
        localStorage.setItem(VERIFIED_KEY, JSON.stringify(lead));
        const leads = JSON.parse(localStorage.getItem(LEADS_KEY) || "[]");
        leads.push(lead);
        localStorage.setItem(LEADS_KEY, JSON.stringify(leads));
      } catch {
        // localStorage may not be available
      }
      setStep("success");
      unlockTimeoutRef.current = setTimeout(() => setStep("unlocked"), 900);
    } else {
      setOtpError(result.error || "Verification failed. Please try again.");
      setOtp("");
      setBusy(false);
    }
  };

  // Auto-verify once all six digits are in
  useEffect(() => {
    if (step === "otp" && otp.length === 6 && !busy) {
      void handleVerify(otp);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [otp, step, busy]);

  const handleResend = async () => {
    if (busy || resendIn > 0) return;
    setBusy(true);
    setOtp("");
    setOtpError(null);
    const result = await sendOtp(normalizePhone(phone));
    setBusy(false);
    if (result.success) {
      setMockActive(Boolean(result.mock));
      setResendIn(30);
    } else {
      setOtpError(result.error ?? "Could not resend the code. Please try again.");
    }
  };

  const handleChangeNumber = () => {
    setOtp("");
    setOtpError(null);
    setResendIn(0);
    setBusy(false);
    setStep("form");
  };

  const locked = step !== "unlocked";
  const overlayVisible = step === "form" || step === "otp" || step === "success";

  return (
    <div className="relative">
      <div
        inert={locked || undefined}
        aria-hidden={locked}
        className={cn(
          "transition-[filter,opacity] duration-700 ease-out",
          locked && "pointer-events-none select-none blur-md opacity-60 max-h-[600px] overflow-hidden"
        )}
      >
        {children}
      </div>

      {locked && (
        <div className="pointer-events-none absolute inset-x-0 bottom-0 h-24 bg-gradient-to-t from-surface-warm to-transparent" />
      )}

      <AnimatePresence>
        {overlayVisible && (
          <motion.div
            className="absolute inset-0 z-10 flex items-center justify-center p-4"
            exit={{ opacity: 0, scale: 0.96 }}
            transition={{ duration: 0.35 }}
          >
            <div
              role="dialog"
              aria-labelledby="calculator-gate-heading"
              className="w-full max-w-md rounded-2xl border border-gray-200 bg-white p-6 sm:p-8 shadow-xl shadow-gray-900/10 text-center"
            >
              <AnimatePresence mode="wait">
                {step === "form" && (
                  <motion.div
                    key="form"
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -8 }}
                    transition={{ duration: 0.2 }}
                  >
                    <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-brand-50">
                      <Lock className="h-6 w-6 text-brand-600" />
                    </div>
                    <h3
                      id="calculator-gate-heading"
                      className="text-xl font-semibold text-gray-900 font-sans"
                    >
                      Unlock the calculator
                    </h3>
                    <p className="mt-1 mb-6 text-sm text-gray-600 font-sans">
                      Enter your name and mobile number to see your EMI instantly.
                    </p>

                    <form onSubmit={handleFormSubmit} className="space-y-4 font-sans">
                      <div>
                        <label
                          htmlFor="gate-name"
                          className="block text-sm font-medium text-gray-700 mb-1 text-left"
                        >
                          Name *
                        </label>
                        <Input
                          ref={nameInputRef}
                          id="gate-name"
                          type="text"
                          placeholder="Your full name"
                          autoComplete="name"
                          value={name}
                          onChange={(e) => {
                            setName(e.target.value);
                            if (formErrors.name) {
                              setFormErrors((prev) => ({ ...prev, name: undefined }));
                            }
                          }}
                        />
                        {formErrors.name && (
                          <p className="mt-1 text-xs text-red-500 text-left">{formErrors.name}</p>
                        )}
                      </div>

                      <div>
                        <label
                          htmlFor="gate-phone"
                          className="block text-sm font-medium text-gray-700 mb-1 text-left"
                        >
                          Mobile Number *
                        </label>
                        <div className="flex">
                          <span className="inline-flex items-center rounded-l-lg border border-r-0 border-gray-300 bg-gray-50 px-3 text-sm text-gray-600">
                            +91
                          </span>
                          <Input
                            id="gate-phone"
                            type="tel"
                            inputMode="tel"
                            autoComplete="tel"
                            placeholder="98765 43210"
                            className="rounded-l-none"
                            value={phone}
                            onChange={(e) => {
                              setPhone(e.target.value);
                              if (formErrors.phone) {
                                setFormErrors((prev) => ({ ...prev, phone: undefined }));
                              }
                            }}
                          />
                        </div>
                        {formErrors.phone && (
                          <p className="mt-1 text-xs text-red-500 text-left">{formErrors.phone}</p>
                        )}
                      </div>

                      <Button type="submit" size="md" className="w-full" disabled={busy}>
                        {busy ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Sending…
                          </>
                        ) : (
                          "Send OTP"
                        )}
                      </Button>
                    </form>
                  </motion.div>
                )}

                {step === "otp" && (
                  <motion.div
                    key="otp"
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -8 }}
                    transition={{ duration: 0.2 }}
                  >
                    <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-brand-50">
                      <ShieldCheck className="h-6 w-6 text-brand-600" />
                    </div>
                    <h3
                      id="calculator-gate-heading"
                      className="text-xl font-semibold text-gray-900 font-sans"
                    >
                      Verify your number
                    </h3>
                    <p className="mt-1 mb-6 text-sm text-gray-600 font-sans">
                      We sent a 6-digit code to{" "}
                      <span className="font-medium text-gray-900">
                        {maskPhone(normalizePhone(phone))}
                      </span>
                    </p>

                    <OtpInput value={otp} onChange={setOtp} disabled={busy} error={!!otpError} />

                    {otpError && (
                      <p role="alert" className="mt-2 text-xs text-red-500 font-sans">
                        {otpError}
                      </p>
                    )}
                    {mockActive && (
                      <p className="mt-2 text-[10px] text-gray-400 font-sans">
                        Dev code: {DEV_OTP_CODE}
                      </p>
                    )}

                    <Button
                      type="button"
                      size="md"
                      className="w-full mt-6"
                      disabled={otp.length !== 6 || busy}
                      onClick={() => handleVerify(otp)}
                    >
                      {busy ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Verifying…
                        </>
                      ) : (
                        "Verify & Unlock"
                      )}
                    </Button>

                    <div className="mt-4 flex items-center justify-between text-sm font-sans">
                      <button
                        type="button"
                        onClick={handleResend}
                        disabled={resendIn > 0 || busy}
                        className="font-medium text-brand-600 hover:text-brand-700 disabled:text-gray-400 disabled:cursor-not-allowed"
                      >
                        {resendIn > 0 ? `Resend in ${resendIn}s` : "Resend OTP"}
                      </button>
                      <button
                        type="button"
                        onClick={handleChangeNumber}
                        disabled={busy}
                        className="text-gray-500 underline hover:text-gray-700 disabled:cursor-not-allowed"
                      >
                        Change number
                      </button>
                    </div>
                  </motion.div>
                )}

                {step === "success" && (
                  <motion.div
                    key="success"
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -8 }}
                    transition={{ duration: 0.2 }}
                  >
                    <CheckCircle className="mx-auto h-12 w-12 text-accent-green mb-4" />
                    <h3
                      id="calculator-gate-heading"
                      className="text-xl font-semibold text-gray-900 font-sans"
                    >
                      Verified!
                    </h3>
                    <p className="mt-1 text-sm text-gray-600 font-sans">
                      Unlocking your calculator…
                    </p>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
