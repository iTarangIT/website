// Persist a completed WhatsApp customer onboarding as a real lead.
//
// ⚠️ This repo is a READ MODEL of the CRM DB (see src/lib/db/schema.ts): it
// cannot add tables/columns. A calc_leads row already exists for this customer
// (inserted when the schemes were generated — its id is carried on the session
// as `leadId`), so we PROMOTE that quote row into a completed lead by writing
// the details collected in-chat back onto it, rather than inserting a new row.
//
//   • customer_name ← the full name the customer confirmed (as per ID)
//   • pincode       ← the delivery pincode they gave
//
// The crm_* columns are intentionally left untouched: they belong to the
// separate CRM hand-off (crm_synced_at IS NULL is how a downstream sync finds
// rows to push), so stamping them here would make the lead look already-synced.
// Email has no column in calc_leads and is only logged by the caller.

import { eq } from "drizzle-orm";
import { db } from "@/lib/db";
import { calcLeads } from "@/lib/db/schema";
import type { OnboardingSession } from "./onboarding-store";

/**
 * Write the onboarding answers onto the customer's calc_leads row.
 * Best-effort: returns true on success, false on any failure (never throws) so
 * a DB hiccup can't break the customer's WhatsApp reply.
 */
export async function persistOnboardingLead(session: OnboardingSession): Promise<boolean> {
  if (!session.leadId) return false; // no quote row to attach the details to

  try {
    const fullName = session.answers.fullName?.trim() || session.customerName;
    const pincode = session.answers.pincode?.trim();

    await db
      .update(calcLeads)
      .set({
        customerName: fullName,
        ...(pincode ? { pincode } : {}),
      })
      .where(eq(calcLeads.id, session.leadId));

    return true;
  } catch (err) {
    console.error("[wa-onboarding] lead persist failed:", err);
    return false;
  }
}
