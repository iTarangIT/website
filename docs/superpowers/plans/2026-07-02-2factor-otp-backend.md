# 2Factor.in OTP Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the mocked OTP service behind the `/how-it-works` calculator gate with real SMS OTP via 2Factor.in AUTOGEN, keeping the API key and session ID server-side.

**Architecture:** Two Next.js route handlers (`POST /api/otp/send`, `POST /api/otp/verify`) call 2Factor's AUTOGEN/VERIFY endpoints; the 2Factor session ID travels in a 10-minute httpOnly cookie scoped to `/api/otp`. A dependency-free server module (`src/lib/otp-server.ts`) holds the 2Factor client, in-memory rate limiting, and mock-mode detection. The client `src/lib/otp.ts` becomes fetch wrappers with an unchanged result shape.

**Tech Stack:** Next.js 16.2.1 route handlers (NextRequest/NextResponse, same style as `src/app/api/elevenlabs/call/route.ts`), no new dependencies. Tests: `npx tsx` script for the pure limiter, `curl` against the dev server in mock mode, existing Playwright scratchpad harness for e2e.

## Global Constraints

- No new npm dependencies.
- Spec: `docs/superpowers/specs/2026-07-02-2factor-otp-backend-design.md` — error copy strings must match its table verbatim.
- Cookie: name `itarang_otp_session`, `httpOnly`, `sameSite: "lax"`, `secure` only in production, `maxAge: 600`, `path: "/api/otp"`.
- Mock mode ⇔ `TWOFACTOR_MOCK === "1"`, or `TWOFACTOR_API_KEY` unset while `NODE_ENV !== "production"`.
- Never send 2Factor's raw `Details` string to the client on failure; log it server-side, return friendly copy.
- Automated route tests require mock mode: append `TWOFACTOR_MOCK=1` to `.env.local` while testing (Next dev reloads env file changes); remove it for the final live smoke test.
- The user's dev server runs on port 3000 — do not kill it; do not start a second dev server (Next 16 refuses).

---

### Task 1: Server module `src/lib/otp-server.ts`

**Files:**
- Create: `src/lib/otp-server.ts`
- Test: `<scratchpad>/test-otp-server.ts` (throwaway, not committed)

**Interfaces:**
- Consumes: nothing from the repo (dependency-free by design so `tsx` can run it outside Next; env vars only).
- Produces (used by Tasks 2–3):
  - `isMockMode(): boolean`
  - `checkSendAllowed(phone: string, now?: number): { allowed: boolean; error?: string }`
  - `recordSend(phone: string, now?: number): void`
  - `recordVerifyAttempt(sessionId: string, now?: number): boolean` — false once attempts exceed 5
  - `clearVerifyAttempts(sessionId: string): void`
  - `twoFactorSend(e164Phone: string): Promise<{ success: boolean; sessionId?: string; error?: string; status?: number }>`
  - `twoFactorVerify(sessionId: string, code: string): Promise<{ success: boolean; error?: string; status?: number }>`

- [ ] **Step 1: Write the failing limiter test** at `<scratchpad>/test-otp-server.ts`:

```ts
// Run from D:\itarang_website with: npx tsx <scratchpad>/test-otp-server.ts
const mod = await import("file:///D:/itarang_website/src/lib/otp-server.ts");
const { checkSendAllowed, recordSend, recordVerifyAttempt, clearVerifyAttempts } = mod;

let failures = 0;
function expect(label: string, cond: boolean) {
  console.log(`${cond ? "PASS" : "FAIL"}: ${label}`);
  if (!cond) failures++;
}

const t0 = 1_000_000_000_000;
const phone = "+919000000001";

expect("first send allowed", checkSendAllowed(phone, t0).allowed === true);
recordSend(phone, t0);
expect("send 5s later blocked (cooldown)", checkSendAllowed(phone, t0 + 5_000).allowed === false);
expect("cooldown error copy", /wait a moment/i.test(checkSendAllowed(phone, t0 + 5_000).error ?? ""));
expect("send 31s later allowed", checkSendAllowed(phone, t0 + 31_000).allowed === true);

// hourly cap: 5 sends spaced 60s apart, 6th blocked
for (let i = 1; i < 5; i++) recordSend(phone, t0 + i * 60_000);
const sixth = checkSendAllowed(phone, t0 + 5 * 60_000);
expect("6th send within the hour blocked", sixth.allowed === false);
expect("hourly error copy", /too many/i.test(sixth.error ?? ""));
expect("send allowed after window expires", checkSendAllowed(phone, t0 + 61 * 60_000).allowed === true);
expect("other phone unaffected", checkSendAllowed("+919000000002", t0 + 5_000).allowed === true);

const sid = "session-abc";
for (let i = 0; i < 5; i++) expect(`verify attempt ${i + 1} allowed`, recordVerifyAttempt(sid, t0) === true);
expect("verify attempt 6 blocked", recordVerifyAttempt(sid, t0) === false);
clearVerifyAttempts(sid);
expect("attempts reset after clear", recordVerifyAttempt(sid, t0) === true);

if (failures) { console.error(`${failures} failure(s)`); process.exit(1); }
console.log("ALL PASS");
```

- [ ] **Step 2: Run it to verify it fails** — `npx tsx <scratchpad>/test-otp-server.ts` → expected: module-not-found error for `src/lib/otp-server.ts`.

- [ ] **Step 3: Implement `src/lib/otp-server.ts`:**

```ts
// Server-only helpers for the OTP routes. Keep this module dependency-free
// (env vars only) so it can be exercised directly with tsx outside Next.

const TWOFACTOR_BASE = "https://2factor.in/API/V1";

const SEND_COOLDOWN_MS = 30_000;
const SEND_WINDOW_MS = 3_600_000;
const SEND_WINDOW_LIMIT = 5;
const MAX_VERIFY_ATTEMPTS = 5;
const ATTEMPT_TTL_MS = 15 * 60_000;

// Per-instance state: resets on redeploy and is not shared across serverless
// instances — an accepted limitation for current traffic (see design spec).
const sendHistory = new Map<string, number[]>();
const verifyAttempts = new Map<string, { count: number; ts: number }>();

export function isMockMode(): boolean {
  if (process.env.TWOFACTOR_MOCK === "1") return true;
  return !process.env.TWOFACTOR_API_KEY && process.env.NODE_ENV !== "production";
}

export function checkSendAllowed(
  phone: string,
  now: number = Date.now()
): { allowed: boolean; error?: string } {
  const recent = (sendHistory.get(phone) ?? []).filter((t) => t > now - SEND_WINDOW_MS);
  sendHistory.set(phone, recent);
  const last = recent[recent.length - 1];
  if (last !== undefined && now - last < SEND_COOLDOWN_MS) {
    return { allowed: false, error: "Please wait a moment before requesting another code." };
  }
  if (recent.length >= SEND_WINDOW_LIMIT) {
    return { allowed: false, error: "Too many attempts. Please try again in a few minutes." };
  }
  return { allowed: true };
}

export function recordSend(phone: string, now: number = Date.now()): void {
  const recent = (sendHistory.get(phone) ?? []).filter((t) => t > now - SEND_WINDOW_MS);
  recent.push(now);
  sendHistory.set(phone, recent);
}

/** Counts an attempt; returns false once the session has used up its 5 tries. */
export function recordVerifyAttempt(sessionId: string, now: number = Date.now()): boolean {
  for (const [key, entry] of verifyAttempts) {
    if (now - entry.ts > ATTEMPT_TTL_MS) verifyAttempts.delete(key);
  }
  const entry = verifyAttempts.get(sessionId) ?? { count: 0, ts: now };
  entry.count += 1;
  entry.ts = now;
  verifyAttempts.set(sessionId, entry);
  return entry.count <= MAX_VERIFY_ATTEMPTS;
}

export function clearVerifyAttempts(sessionId: string): void {
  verifyAttempts.delete(sessionId);
}

interface TwoFactorResponse {
  Status?: string;
  Details?: string;
}

async function callTwoFactor(url: string): Promise<TwoFactorResponse | null> {
  try {
    const res = await fetch(url, { cache: "no-store" });
    return (await res.json().catch(() => null)) as TwoFactorResponse | null;
  } catch {
    return null;
  }
}

export async function twoFactorSend(
  e164Phone: string
): Promise<{ success: boolean; sessionId?: string; error?: string; status?: number }> {
  const key = process.env.TWOFACTOR_API_KEY;
  if (!key) {
    return { success: false, error: "OTP service is temporarily unavailable.", status: 500 };
  }
  const template = process.env.TWOFACTOR_TEMPLATE_NAME;
  const url = `${TWOFACTOR_BASE}/${key}/SMS/${encodeURIComponent(e164Phone)}/AUTOGEN${
    template ? `/${encodeURIComponent(template)}` : ""
  }`;
  const data = await callTwoFactor(url);
  if (data?.Status === "Success" && data.Details) {
    return { success: true, sessionId: data.Details };
  }
  console.error(`[otp] 2Factor send failed for ${e164Phone}:`, data?.Details ?? "network/parse error");
  return { success: false, error: "Couldn't send the code. Please try again.", status: 502 };
}

export async function twoFactorVerify(
  sessionId: string,
  code: string
): Promise<{ success: boolean; error?: string; status?: number }> {
  const key = process.env.TWOFACTOR_API_KEY;
  if (!key) {
    return { success: false, error: "OTP service is temporarily unavailable.", status: 500 };
  }
  const url = `${TWOFACTOR_BASE}/${key}/SMS/VERIFY/${encodeURIComponent(sessionId)}/${encodeURIComponent(code)}`;
  const data = await callTwoFactor(url);
  const details = data?.Details ?? "";
  // 2Factor signals mismatch/expiry via Details (HTTP status varies) — branch on the string.
  if (data?.Status === "Success" && /matched/i.test(details)) return { success: true };
  if (/mismatch/i.test(details)) {
    return { success: false, error: "Incorrect code. Please try again.", status: 400 };
  }
  if (/expired/i.test(details)) {
    return { success: false, error: "That code expired. Please resend.", status: 400 };
  }
  console.error(`[otp] 2Factor verify failed:`, details || "network/parse error");
  return { success: false, error: "Verification failed. Please try again.", status: 502 };
}
```

- [ ] **Step 4: Run the test again** — `npx tsx <scratchpad>/test-otp-server.ts` → expected: `ALL PASS`, exit 0.

- [ ] **Step 5: Commit** — `git add src/lib/otp-server.ts && git commit -m "feat(otp): server module for 2Factor calls + in-memory rate limiting"`

---

### Task 2: Send route `src/app/api/otp/send/route.ts`

**Files:**
- Create: `src/app/api/otp/send/route.ts`
- Modify: `.env.local` (append `TWOFACTOR_MOCK=1` for testing — temporary, removed in Task 5)

**Interfaces:**
- Consumes: Task 1 exports; `isValidIndianMobile`, `normalizePhone`, `DEV_OTP_CODE` from `@/lib/otp` (existing pure helpers).
- Produces: `POST /api/otp/send` accepting `{ phone: string }` → `{ success: true, mock?: true }` + `Set-Cookie: itarang_otp_session=…`, or `{ success: false, error: string }` with status 400/429/5xx. Cookie name constant `OTP_COOKIE = "itarang_otp_session"` (duplicated verbatim in Task 3's route).

- [ ] **Step 1: Enable mock mode** — append `TWOFACTOR_MOCK=1` to `.env.local`. The running dev server reloads env automatically.

- [ ] **Step 2: Probe the not-yet-existing route (failing test)**:

```bash
curl -si -X POST http://localhost:3000/api/otp/send -H "Content-Type: application/json" -d "{\"phone\":\"9123456780\"}"
```

Expected: `404`.

- [ ] **Step 3: Implement the route:**

```ts
import { NextRequest, NextResponse } from "next/server";
import { DEV_OTP_CODE, isValidIndianMobile, normalizePhone } from "@/lib/otp";
import { checkSendAllowed, isMockMode, recordSend, twoFactorSend } from "@/lib/otp-server";

const OTP_COOKIE = "itarang_otp_session";

export async function POST(req: NextRequest) {
  const body = await req.json().catch(() => null);
  const phone = typeof body?.phone === "string" ? body.phone : "";
  if (!isValidIndianMobile(phone)) {
    return NextResponse.json(
      { success: false, error: "Enter a valid 10-digit Indian mobile number" },
      { status: 400 },
    );
  }
  const e164 = normalizePhone(phone);

  const gate = checkSendAllowed(e164);
  if (!gate.allowed) {
    return NextResponse.json({ success: false, error: gate.error }, { status: 429 });
  }

  let sessionId: string;
  let mock = false;
  if (isMockMode()) {
    sessionId = "mock";
    mock = true;
    console.info(`[otp] MOCK send to ${e164} — code ${DEV_OTP_CODE}`);
  } else {
    const sent = await twoFactorSend(e164);
    if (!sent.success || !sent.sessionId) {
      return NextResponse.json(
        { success: false, error: sent.error ?? "Couldn't send the code. Please try again." },
        { status: sent.status ?? 502 },
      );
    }
    sessionId = sent.sessionId;
  }
  recordSend(e164);

  const res = NextResponse.json(mock ? { success: true, mock: true } : { success: true });
  res.cookies.set(OTP_COOKIE, sessionId, {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    maxAge: 600,
    path: "/api/otp",
  });
  return res;
}
```

- [ ] **Step 4: Route-level tests (mock mode, distinct phones so rate-limit state doesn't cross-contaminate):**

```bash
# happy path → 200, {"success":true,"mock":true}, Set-Cookie itarang_otp_session=mock; Path=/api/otp; HttpOnly
curl -si -X POST http://localhost:3000/api/otp/send -H "Content-Type: application/json" -d "{\"phone\":\"9123456780\"}"
# invalid phone → 400 with the exact copy
curl -si -X POST http://localhost:3000/api/otp/send -H "Content-Type: application/json" -d "{\"phone\":\"12345\"}"
# malformed body → 400
curl -si -X POST http://localhost:3000/api/otp/send -H "Content-Type: application/json" -d "not json"
# immediate repeat for the SAME phone → 429 "Please wait a moment…"
curl -si -X POST http://localhost:3000/api/otp/send -H "Content-Type: application/json" -d "{\"phone\":\"9123456780\"}"
```

- [ ] **Step 5: Commit** — `git add src/app/api/otp/send/route.ts && git commit -m "feat(otp): send route calling 2Factor AUTOGEN, session in httpOnly cookie"`

---

### Task 3: Verify route `src/app/api/otp/verify/route.ts`

**Files:**
- Create: `src/app/api/otp/verify/route.ts`

**Interfaces:**
- Consumes: Task 1 exports; `DEV_OTP_CODE` from `@/lib/otp`; cookie `itarang_otp_session` set by Task 2.
- Produces: `POST /api/otp/verify` accepting `{ code: string }` → `{ success: true }` (cookie cleared) or `{ success: false, error: string }` with 400/429/5xx.

- [ ] **Step 1: Failing probe** — `curl -si -X POST http://localhost:3000/api/otp/verify -H "Content-Type: application/json" -d "{\"code\":\"123456\"}"` → expected `404`.

- [ ] **Step 2: Implement the route:**

```ts
import { NextRequest, NextResponse } from "next/server";
import { DEV_OTP_CODE } from "@/lib/otp";
import { clearVerifyAttempts, isMockMode, recordVerifyAttempt, twoFactorVerify } from "@/lib/otp-server";

const OTP_COOKIE = "itarang_otp_session";

function clearCookie(res: NextResponse) {
  res.cookies.set(OTP_COOKIE, "", {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    maxAge: 0,
    path: "/api/otp",
  });
  return res;
}

export async function POST(req: NextRequest) {
  const body = await req.json().catch(() => null);
  const code = typeof body?.code === "string" ? body.code.trim() : "";
  if (!/^\d{6}$/.test(code)) {
    return NextResponse.json(
      { success: false, error: "Enter the 6-digit code" },
      { status: 400 },
    );
  }

  const sessionId = req.cookies.get(OTP_COOKIE)?.value;
  if (!sessionId) {
    return NextResponse.json(
      { success: false, error: "Your session expired. Please resend the code." },
      { status: 400 },
    );
  }

  if (!recordVerifyAttempt(sessionId)) {
    return clearCookie(
      NextResponse.json(
        { success: false, error: "Too many attempts. Please resend the code." },
        { status: 429 },
      ),
    );
  }

  let result: { success: boolean; error?: string; status?: number };
  if (sessionId === "mock" && isMockMode()) {
    result =
      code === DEV_OTP_CODE
        ? { success: true }
        : { success: false, error: "Incorrect code. Please try again.", status: 400 };
  } else {
    result = await twoFactorVerify(sessionId, code);
  }

  if (result.success) {
    clearVerifyAttempts(sessionId);
    return clearCookie(NextResponse.json({ success: true }));
  }
  return NextResponse.json(
    { success: false, error: result.error ?? "Verification failed. Please try again." },
    { status: result.status ?? 400 },
  );
}
```

- [ ] **Step 3: Route-level tests (cookie jar in scratchpad):**

```bash
J=<scratchpad>/cookies.txt; rm -f "$J"
# no cookie → 400 "Your session expired…"
curl -si -X POST http://localhost:3000/api/otp/verify -H "Content-Type: application/json" -d "{\"code\":\"123456\"}"
# bad code format → 400 "Enter the 6-digit code"
curl -si -X POST http://localhost:3000/api/otp/verify -H "Content-Type: application/json" -d "{\"code\":\"12ab56\"}"
# fresh send (new phone) storing the cookie
curl -s -c "$J" -X POST http://localhost:3000/api/otp/send -H "Content-Type: application/json" -d "{\"phone\":\"9123456781\"}"
# wrong code with cookie → 400 "Incorrect code. Please try again."
curl -si -b "$J" -X POST http://localhost:3000/api/otp/verify -H "Content-Type: application/json" -d "{\"code\":\"000000\"}"
# right code → 200 {"success":true} + Set-Cookie clearing (Max-Age=0)
curl -si -b "$J" -X POST http://localhost:3000/api/otp/verify -H "Content-Type: application/json" -d "{\"code\":\"123456\"}"
# attempt cap: new send (another phone), then 6 wrong codes → 6th returns 429 + cookie cleared
```

- [ ] **Step 4: Commit** — `git add src/app/api/otp/verify/route.ts && git commit -m "feat(otp): verify route with attempt cap and cookie lifecycle"`

---

### Task 4: Client wiring — `src/lib/otp.ts` + `CalculatorGate.tsx`

**Files:**
- Modify: `src/lib/otp.ts` (replace `sendOtp`/`verifyOtp`; keep `DEV_OTP_CODE`, `normalizePhone`, `isValidIndianMobile`, `maskPhone` untouched)
- Modify: `src/components/products/CalculatorGate.tsx`

**Interfaces:**
- Consumes: routes from Tasks 2–3.
- Produces: `sendOtp(phone: string): Promise<OtpResult>` and `verifyOtp(code: string): Promise<OtpResult>` where `OtpResult = { success: boolean; error?: string; mock?: boolean }`. **Breaking change:** `verifyOtp` loses its phone parameter.

- [ ] **Step 1: Rewrite the service half of `src/lib/otp.ts`:**

```ts
export const DEV_OTP_CODE = "123456";

export interface OtpResult {
  success: boolean;
  error?: string;
  mock?: boolean;
}

async function postJson(path: string, body: object): Promise<OtpResult> {
  try {
    const res = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = (await res.json().catch(() => null)) as OtpResult | null;
    if (data && typeof data.success === "boolean") return data;
    return { success: false, error: "Something went wrong. Please try again." };
  } catch {
    return { success: false, error: "Couldn't reach the server. Check your connection and try again." };
  }
}

export function sendOtp(phone: string): Promise<OtpResult> {
  return postJson("/api/otp/send", { phone });
}

export function verifyOtp(code: string): Promise<OtpResult> {
  return postJson("/api/otp/verify", { code });
}
```

(The `delay` helper and old mock bodies are deleted; the pure phone helpers below them stay byte-identical.)

- [ ] **Step 2: Update `CalculatorGate.tsx`:**
  1. Add state: `const [mockActive, setMockActive] = useState(false);`
  2. In `handleFormSubmit` success branch: `setMockActive(Boolean(result.mock));` before `setStep("otp")`.
  3. In `handleResend`: capture the result; on success `setMockActive(Boolean(result.mock))` and start the countdown, on failure `setOtpError(result.error ?? "Could not resend the code. Please try again.")` and do NOT reset the countdown.
  4. `handleVerify`: `verifyOtp(code)` replaces `verifyOtp(normalizePhone(phone), code)`.
  5. Dev-hint block: replace the `process.env.NODE_ENV === "development"` condition with `mockActive`.
  6. `normalizePhone` stays imported (still used for `maskPhone(normalizePhone(phone))` and the localStorage lead record).

- [ ] **Step 3: Type-check** — `npx tsc --noEmit` → expected: clean (a leftover two-arg `verifyOtp` call would fail here).

- [ ] **Step 4: Commit** — `git add src/lib/otp.ts src/components/products/CalculatorGate.tsx && git commit -m "feat(otp): point calculator gate at the real OTP API routes"`

---

### Task 5: Env docs, e2e verification, live smoke test

**Files:**
- Modify: `.env.local.example` (document the three vars)
- Modify: `.env.local` (remove the temporary `TWOFACTOR_MOCK=1` before the live smoke test)

- [ ] **Step 1: Append to `.env.local.example`:**

```
# ---- 2Factor.in SMS OTP (calculator gate on /how-it-works) ----
# Server-side API key from https://2factor.in dashboard.
TWOFACTOR_API_KEY=
# Optional: named DLT-approved OTP template for branded SMS wording.
TWOFACTOR_TEMPLATE_NAME=
# Optional: set to 1 to force mock mode (code 123456, no SMS sent, no credits used).
TWOFACTOR_MOCK=
```

- [ ] **Step 2: Playwright e2e in mock mode** — update the scratchpad `verify-gate.js` expectations: the dev-code hint now appears only after send responds with `mock: true`; wrong-code error copy is unchanged; full flow (gate → form → OTP `123456` → unlocked → localStorage keys → reload skip) must still pass against `http://localhost:3000/how-it-works`. Run: `node <scratchpad>/verify-gate.js` → expected `DONE` with all PASS lines.

- [ ] **Step 3: Run `npx tsc --noEmit` and `npm run lint`** — expected: clean (build stays broken on the pre-existing GROQ_API_KEY issue, unrelated).

- [ ] **Step 4: Commit** — `git add .env.local.example && git commit -m "docs(otp): document 2Factor env vars"`

- [ ] **Step 5: Live smoke test (user in the loop):** remove `TWOFACTOR_MOCK=1` from `.env.local`, confirm `TWOFACTOR_API_KEY` is set there, then the user opens `/how-it-works` fresh (clear the localStorage flag), enters their real number, receives a real SMS, verifies, calculator unlocks. Confirm no "Dev code" hint appeared and the 2Factor dashboard shows one SMS consumed.

---

## Self-Review (done at write time)

- **Spec coverage:** send route (spec §1) → Task 2; verify route (§2) → Task 3; mock mode (§3) → Tasks 1–3; client wrappers (§4) → Task 4; gate tweak (§5) → Task 4; env example (§6) → Task 5; error-copy table → embedded verbatim in Tasks 1–3 code; testing section → Tasks 1–5 steps.
- **Placeholders:** none — every code step carries full code, every test step an exact command.
- **Type consistency:** `OtpResult` shape matches route JSON; `verifyOtp(code)` single-arg change is applied in its only call site (`CalculatorGate.handleVerify`); cookie constant duplicated intentionally in both routes (kept in sync by the Global Constraints line).
