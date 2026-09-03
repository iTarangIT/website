/* ══════════════════════════════════════════════════════════════════════════
 * DEALER NETWORK — read model of the CRM's dealer tables on the shared RDS.
 *
 * Like schema.ts, this declares columns of tables the CRM repo owns. The
 * website only SELECTs from them; never run migrations from here.
 *
 * Only location and status columns are declared on purpose. The real tables
 * also hold owner contact details, bank accounts and tax ids — leave those
 * out so the website cannot select them even by accident.
 * ══════════════════════════════════════════════════════════════════════════ */

import { boolean, doublePrecision, integer, jsonb, pgTable, text, timestamp, uuid, varchar } from "drizzle-orm/pg-core";

export const dealers = pgTable("dealers", {
  id: integer("id").primaryKey(),
  dealerId: varchar("dealer_id", { length: 255 }),
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
