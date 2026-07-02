# 2Factor.in OTP Backend for the Calculator Gate — Design

**Date:** 2026-07-02
**Status:** Approved by user
**Replaces:** the mocked `sendOtp`/`verifyOtp` in `src/lib/otp.ts` (UI shipped earlier; see `C:\Users\adity\.claude\plans\add-an-otp-gated-lead-steady-kettle.md` "Later" section)

## Goal

Wire the OTP-gated EMI calculator (`/how-it-works`) to real SMS delivery via 2Factor.in, keeping the existing UI contract and keeping the API key server-side.

## Decisions (made with user)

- 2Factor account and API key are ready; key goes in `.env.local` as `TWOFACTOR_API_KEY`.
- **AUTOGEN mode**: 2Factor generates, sends, and stores the OTP; we verify against their session ID. No OTP state on our server.
- **Leads stay in localStorage only** — no Supabase insert now (explicitly deferred again by user).
- **Default 2Factor OTP SMS template**; optional `TWOFACTOR_TEMPLATE_NAME` env var for a branded DLT template later, no code change needed.
- **Two route handlers + httpOnly cookie** for the session ID (user-selected over JSON-returned session ID and single-route variants).

## Architecture

```
Browser                    Server                      2Factor
  |  POST /api/otp/send      |                            |
  |  {phone} ------------->  | GET .../SMS/+91xxx/AUTOGEN |
  |                          | -------------------------> |
  |                          | <-- {Details: sessionId}   |
  |  <-- 200 {success, mock?}|                            |
  |      Set-Cookie: itarang_otp_session (10 min, httpOnly)
  |                          |                            |
  |  POST /api/otp/verify    |                            |
  |  {code} -------------->  | GET .../VERIFY/{sid}/{code}|
  |   (cookie sent auto)     | -------------------------> |
  |  <-- 200 / 4xx + error   | cookie cleared on match    |
```

## Components

### 1. `src/app/api/otp/send/route.ts` (new)

- `POST { phone: string }` → validate `isValidIndianMobile`, normalize with `normalizePhone`.
- Call `GET https://2factor.in/API/V1/{TWOFACTOR_API_KEY}/SMS/{e164Phone}/AUTOGEN` — append `/{TWOFACTOR_TEMPLATE_NAME}` when set. `cache: "no-store"`.
- 2Factor success (`Status === "Success"`, `Details` = session ID): set cookie `itarang_otp_session` — `httpOnly`, `sameSite: "lax"`, `secure` when `NODE_ENV === "production"`, `maxAge: 600`, `path: "/api/otp"` — respond `{ success: true, mock?: boolean }`.
- 2Factor error → `{ success: false, error: <friendly copy> }` with status 502 (or 400 for invalid-number responses).
- **Rate limiting** (module-level in-memory `Map` keyed by E.164 phone):
  - 30 s cooldown between sends per phone (mirrors the UI resend timer).
  - Max 5 sends per phone per rolling hour.
  - Exceeded → 429 `{ success: false, error }`.
  - Known limitation: per-instance memory; resets on redeploy and is not shared across serverless instances. Acceptable for current traffic; revisit with Upstash/Redis if abused.

### 2. `src/app/api/otp/verify/route.ts` (new)

- `POST { code: string }` → require exactly 6 digits.
- Read `itarang_otp_session` cookie. Missing → 400 "Your session expired. Please resend the code."
- Call `GET https://2factor.in/API/V1/{key}/SMS/VERIFY/{sessionId}/{code}`.
  - `Details === "OTP Matched"` → clear cookie, `{ success: true }`.
  - `"OTP Mismatch"` → 400 "Incorrect code. Please try again."
  - `"OTP Expired"` → 400 "That code expired. Please resend."
  - Note: 2Factor may return these with HTTP 200 or 400 — branch on the `Details` string, not the HTTP status.
- Backstop: max 5 verify attempts per session ID (in-memory counter); exceeded → 429 + clear cookie.

### 3. Mock mode (dev/testing)

- Active when `TWOFACTOR_MOCK === "1"`, or when `TWOFACTOR_API_KEY` is unset **and** `NODE_ENV !== "production"`.
- Send: no external call, cookie value `"mock"`, respond `{ success: true, mock: true }`, log dev code `123456`.
- Verify: cookie `"mock"` (never valid against the real API by construction) → compare against `123456`.
- Production with no key and no mock flag → 500 "OTP service is not configured."

### 4. `src/lib/otp.ts` (edit)

- `sendOtp(phone)` / `verifyOtp(code)` become `fetch` wrappers over the two routes (same-origin, JSON), returning `{ success, error?, mock? }`. Network failure → `{ success: false, error: "Couldn't reach the server. Check your connection and try again." }`.
- `verifyOtp` no longer needs the phone argument (session is in the cookie) — signature becomes `verifyOtp(code)`.
- `normalizePhone`, `isValidIndianMobile`, `maskPhone` unchanged (pure, shared client/server).
- `DEV_OTP_CODE` stays exported for the mock hint + tests.

### 5. `src/components/products/CalculatorGate.tsx` (minimal edit)

- Track `mockActive` from the `sendOtp` response; render the "Dev code: 123456" hint only when `mockActive` (replaces the `NODE_ENV === "development"` check).
- Update the `verifyOtp` call site for the new signature. All other behavior (steps, resend timer, error display, localStorage flag) unchanged.

### 6. `.env.local.example` (edit)

```
TWOFACTOR_API_KEY=            # from 2factor.in dashboard
TWOFACTOR_TEMPLATE_NAME=      # optional: named OTP template for branded SMS
TWOFACTOR_MOCK=               # optional: "1" forces mock mode (code 123456, no SMS)
```

## Error handling summary

| Failure | User sees |
| --- | --- |
| Invalid phone (server re-check) | "Enter a valid 10-digit Indian mobile number" |
| Rate limited | "Too many attempts. Please try again in a few minutes." |
| 2Factor down / network error | "Couldn't send the code. Please try again." |
| Wrong code | "Incorrect code. Please try again." |
| Expired session/code | "That code expired. Please resend." |
| No API key in production | "OTP service is temporarily unavailable." |

## Security notes

- API key only ever read in route handlers (server). Never in client bundle.
- Session ID never exposed to page JS (httpOnly cookie, scoped to `/api/otp`).
- Server re-validates phone and code format; never interpolates unvalidated input into the 2Factor URL (phone is rebuilt from digits, code checked `/^\d{6}$/`).
- The gate remains a lead-capture UX gate, not an auth boundary — the calculator itself is not sensitive.

## Testing

1. Automated (Playwright, mock mode via `TWOFACTOR_MOCK=1`): full happy path, wrong code, missing-cookie verify, resend cooldown 429, rate-limit copy.
2. `npx tsc --noEmit`.
3. Live smoke test (user): real key in `.env.local`, real phone number, receive SMS, verify, calculator unlocks. Balance visible in 2Factor dashboard should decrement by 1.

## Out of scope

- Supabase lead insert (deferred by user, again — hook point stays `handleVerify` success branch in `CalculatorGate.tsx` / `insertLead` in `src/lib/supabase/client.ts:123`).
- Distributed rate limiting (Upstash/Redis).
- TTL on the localStorage verified flag.
