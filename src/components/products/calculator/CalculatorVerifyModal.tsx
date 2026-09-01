"use client";

// Per-search WhatsApp OTP verification modal for the public Loan Calculator.
//
// Unlike the old CalculatorGate (a one-time permanent unlock), this modal is
// opened every time the visitor clicks "Calculate schemes". Each successful
// verification is single-use: it mints a fresh signed calculator cookie for
// exactly one calculation, so every search requires a new OTP.

import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { CheckCircle, Loader2, ShieldCheck, X } from "lucide-react";
import Input from "@/components/ui/Input";
import Button from "@/components/ui/Button";
import OtpInput from "@/components/shared/OtpInput";
import {
  DEV_OTP_CODE,
  isValidIndianMobile,
  maskPhone,
  normalizePhone,
  sendWhatsappOtp as sendOtp,
  verifyWhatsappOtp as verifyOtp,
} from "@/lib/whatsapp-otp";
import { EVENTS, trackEvent } from "@/lib/analytics";

export interface VerifiedLead {
  name: string;
  phone: string; // +91XXXXXXXXXX
}

interface Props {
  open: boolean;
  onClose: () => void;
  onVerified: (lead: VerifiedLead) => void;
  initialName?: string;
  initialPhone?: string;
}

type Step = "form" | "otp" | "success";

export default function CalculatorVerifyModal({
  open,
  onClose,
  onVerified,
  initialName = "",
  initialPhone = "",
}: Props) {
  const [step, setStep] = useState<Step>("form");
  const [name, setName] = useState(initialName);
  const [phone, setPhone] = useState(initialPhone);
  const [formErrors, setFormErrors] = useState<{ name?: string; phone?: string }>({});
  const [otp, setOtp] = useState("");
  const [otpError, setOtpError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [resendIn, setResendIn] = useState(0);
  const [mockActive, setMockActive] = useState(false);

  const nameInputRef = useRef<HTMLInputElement>(null);

  // Reset to a clean form each time the modal opens (single-use verification).
  useEffect(() => {
    if (open) {
      setStep("form");
      setName(initialName);
      setPhone(initialPhone);
      setFormErrors({});
      setOtp("");
      setOtpError(null);
      setBusy(false);
      setResendIn(0);
    }
  }, [open, initialName, initialPhone]);

  useEffect(() => {
    if (open && step === "form") nameInputRef.current?.focus();
  }, [open, step]);

  // Resend countdown
  useEffect(() => {
    if (step !== "otp" || resendIn <= 0) return;
    const t = setTimeout(() => setResendIn((s) => s - 1), 1000);
    return () => clearTimeout(t);
  }, [step, resendIn]);

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
    const result = await sendOtp(normalizePhone(phone), name.trim());
    setBusy(false);
    if (result.success) {
      // Reported on a delivered OTP, not on the button press. A send that
      // failed is a step the visitor never actually reached, and counting it
      // would hide a broken gate as a drop-off.
      trackEvent(EVENTS.otpRequested, { lead_source: "loan_calculator" });
      setMockActive(result.data?.waStatus === "dev_hardcoded");
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
      trackEvent(EVENTS.otpVerified, { lead_source: "loan_calculator" });
      setStep("success");
      // Brief success flash, then hand the verified lead back to the caller.
      setTimeout(() => {
        onVerified({ name: name.trim(), phone: normalizePhone(phone) });
      }, 700);
    } else {
      setOtpError(result.error || "Verification failed. Please try again.");
      setOtp("");
      setBusy(false);
    }
  };

  // Auto-verify once all six digits are in
  useEffect(() => {
    if (open && step === "otp" && otp.length === 6 && !busy) {
      void handleVerify(otp);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [otp, step, busy, open]);

  const handleResend = async () => {
    if (busy || resendIn > 0) return;
    setBusy(true);
    setOtp("");
    setOtpError(null);
    const result = await sendOtp(normalizePhone(phone), name.trim());
    setBusy(false);
    if (result.success) {
      setMockActive(result.data?.waStatus === "dev_hardcoded");
      setResendIn(30);
    } else {
      setOtpError(result.error ?? "Could not resend the code. Please try again.");
    }
  };

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
        >
          <div
            className="absolute inset-0 bg-gray-900/50 backdrop-blur-sm"
            onClick={busy ? undefined : onClose}
          />
          <motion.div
            role="dialog"
            aria-modal="true"
            aria-labelledby="calc-verify-heading"
            initial={{ opacity: 0, scale: 0.96, y: 8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: 8 }}
            transition={{ duration: 0.2 }}
            className="relative w-full max-w-md rounded-2xl border border-gray-200 bg-white p-6 sm:p-8 text-center shadow-xl shadow-gray-900/10"
          >
            {step !== "success" && (
              <button
                type="button"
                onClick={onClose}
                disabled={busy}
                aria-label="Close"
                className="absolute right-4 top-4 text-gray-400 hover:text-gray-600 disabled:cursor-not-allowed"
              >
                <X className="h-5 w-5" />
              </button>
            )}

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
                    <ShieldCheck className="h-6 w-6 text-brand-600" />
                  </div>
                  <h3 id="calc-verify-heading" className="text-xl font-semibold text-gray-900 font-sans">
                    Verify to see your schemes
                  </h3>
                  <p className="mt-1 mb-6 text-sm text-gray-600 font-sans">
                    Enter your name and mobile number — we&apos;ll send a
                    one-time code by SMS to confirm this search.
                  </p>

                  <form onSubmit={handleFormSubmit} className="space-y-4 font-sans">
                    <div>
                      <label htmlFor="cv-name" className="block text-sm font-medium text-gray-700 mb-1 text-left">
                        Name *
                      </label>
                      <Input
                        ref={nameInputRef}
                        id="cv-name"
                        type="text"
                        placeholder="Your full name"
                        autoComplete="name"
                        value={name}
                        onChange={(e) => {
                          setName(e.target.value);
                          if (formErrors.name) setFormErrors((p) => ({ ...p, name: undefined }));
                        }}
                      />
                      {formErrors.name && (
                        <p className="mt-1 text-xs text-red-500 text-left">{formErrors.name}</p>
                      )}
                    </div>

                    <div>
                      <label htmlFor="cv-phone" className="block text-sm font-medium text-gray-700 mb-1 text-left">
                        Mobile Number *
                      </label>
                      <div className="flex">
                        <span className="inline-flex items-center rounded-l-lg border border-r-0 border-gray-300 bg-gray-50 px-3 text-sm text-gray-600">
                          +91
                        </span>
                        <Input
                          id="cv-phone"
                          type="tel"
                          inputMode="tel"
                          autoComplete="tel"
                          placeholder="98765 43210"
                          className="rounded-l-none"
                          value={phone}
                          onChange={(e) => {
                            setPhone(e.target.value);
                            if (formErrors.phone) setFormErrors((p) => ({ ...p, phone: undefined }));
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
                  <h3 id="calc-verify-heading" className="text-xl font-semibold text-gray-900 font-sans">
                    Verify your number
                  </h3>
                  <p className="mt-1 mb-6 text-sm text-gray-600 font-sans">
                    We sent a 6-digit code by SMS to{" "}
                    <span className="font-medium text-gray-900">{maskPhone(normalizePhone(phone))}</span>
                  </p>

                  <OtpInput value={otp} onChange={setOtp} disabled={busy} error={!!otpError} />

                  {otpError && (
                    <p role="alert" className="mt-2 text-xs text-red-500 font-sans">
                      {otpError}
                    </p>
                  )}
                  {mockActive && (
                    <p className="mt-2 text-[10px] text-gray-400 font-sans">Dev code: {DEV_OTP_CODE}</p>
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
                      "Verify & see schemes"
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
                      onClick={() => setStep("form")}
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
                  <h3 id="calc-verify-heading" className="text-xl font-semibold text-gray-900 font-sans">
                    Verified!
                  </h3>
                  <p className="mt-1 text-sm text-gray-600 font-sans">Fetching your schemes…</p>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
