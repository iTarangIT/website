/* ══════════════════════════════════════════════════════════════════════════
 * DEALER NETWORK — read model of the CRM's dealer tables on the shared RDS.
 *
 * Like schema.ts, this declares columns of tables the CRM repo owns. The
 * website only SELECTs from them; never run migrations from here.
 *
 * Location, status and PUBLISHED CONTACT columns are declared on purpose.
 * Everything else is left out so the website cannot select it even by accident.
 *
 * The contact columns are here because /for-dealers now answers "who do I
 * call?": company_name, contact_phone and owner_phone are shown to the public
 * in the nearest-dealer results, the way any store locator shows a dealer.
 * Exactly those three, and only for dealers whose onboarding_status is active.
 *
 * Still deliberately absent, and to stay absent: bank_* , *_number (PAN, GST,
 * CIN, Aadhaar), owner_email, and every operator, agreement and audit column.
 * If you find yourself adding one, that is a decision to publish it — take it
 * to a human first.
 * ══════════════════════════════════════════════════════════════════════════ */

import { boolean, doublePrecision, integer, jsonb, pgTable, text, timestamp, uuid, varchar } from "drizzle-orm/pg-core";

export const dealers = pgTable("dealers", {
  id: integer("id").primaryKey(),
  dealerId: varchar("dealer_id", { length: 255 }),
  /** Trading name, shown publicly in nearest-dealer results. */
  companyName: varchar("company_name", { length: 255 }),
  /** Published fallback when the application has no contact_phone. */
  ownerPhone: varchar("owner_phone", { length: 255 }),
  onboardingStatus: varchar("onboarding_status", { length: 255 }).notNull(),
  applicationId: varchar("application_id", { length: 255 }),
  /** Either `{ "address": "..." }` or a bare JSON string; see readAddress(). */
  registeredAddress: jsonb("registered_address"),
  activatedAt: timestamp("activated_at", { withTimezone: true }),
  dealerType: varchar("dealer_type", { length: 255 }),
});

export const dealerOnboardingApplications = pgTable("dealer_onboarding_applications", {
  id: uuid("id").primaryKey(),
  onboardingStatus: varchar("onboarding_status", { length: 255 }).notNull(),
  /** Free text, usually a JSON string `{"address": "..."}`. */
  businessAddress: text("business_address"),
  city: varchar("city", { length: 255 }),
  state: varchar("state", { length: 255 }),
  pincode: varchar("pincode", { length: 255 }),
  /** Trading name as given on the application. */
  companyName: text("company_name"),
  /** The dealer's designated business contact; preferred over owner_phone. */
  contactPhone: varchar("contact_phone", { length: 255 }),
  isBranchDealer: boolean("is_branch_dealer"),
  submittedAt: timestamp("submitted_at"),
});

/** CRM city master: 1,250 names with a state code; coordinates on some rows. */
export const crmCities = pgTable("cities", {
  id: text("id").primaryKey(),
  name: text("name").notNull(),
  stateCode: text("state_code").notNull(),
  lat: doublePrecision("lat"),
  lng: doublePrecision("lng"),
});

export const crmCityAliases = pgTable("city_aliases", {
  aliasLower: text("alias_lower").notNull(),
  cityId: text("city_id").notNull(),
});
