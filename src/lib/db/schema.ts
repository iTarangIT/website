/* ══════════════════════════════════════════════════════════════════════════
 * LOAN CALCULATOR — mirror of the CRM's calc_* schema (migrations E-177/E-178,
 * applied to the shared AWS RDS database-2 from the CRM repo).
 *
 * This file is a READ MODEL of an existing database. Do NOT run migrations or
 * drizzle-kit push from this repo — the CRM repo owns the calc_* schema.
 * The website only READS config tables and INSERTS into calc_leads.
 *
 * Money in PAISE (1 rupee = 100); rates as numeric. Config is effective-dated
 * (valid_from/valid_to) + versioned (calc_config_versions).
 * ══════════════════════════════════════════════════════════════════════════ */

import {
  pgTable,
  pgEnum,
  serial,
  bigserial,
  bigint,
  integer,
  numeric,
  boolean,
  text,
  timestamp,
  jsonb,
  uuid,
  varchar,
  index,
  uniqueIndex,
} from "drizzle-orm/pg-core";

export const calcEngineVariant = pgEnum("calc_engine_variant", ["A", "B"]);
export const calcRecordStatus = pgEnum("calc_record_status", ["active", "disabled"]);
export const calcCoverageType = pgEnum("calc_coverage_type", ["CITY", "PAN_INDIA"]);
export const calcComponentKind = pgEnum("calc_component_kind", [
  "battery",
  "charger",
  "harness",
  "soc",
  "iot",
]);
export const calcLeadFilterOutcome = pgEnum("calc_lead_filter_outcome", [
  "qualified",
  "stretch_only",
  "none",
]);

// One row per published state of config. Every admin save (in the CRM) inserts
// a new version and stamps the changed rows' valid_from with it.
export const calcConfigVersions = pgTable(
  "calc_config_versions",
  {
    id: bigserial("id", { mode: "number" }).primaryKey(),
    createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
    createdBy: uuid("created_by").notNull(),
    note: text("note"),
    changeSummary: jsonb("change_summary"),
  },
  (t) => ({
    createdAtIdx: index("calc_config_versions_created_at_idx").on(t.createdAt),
  }),
);

// Global settings (effective-dated, single current row). dealer margin, near-best
// window, disclaimer, filter-required toggles, Card-2 footer contacts.
export const calcSettings = pgTable(
  "calc_settings",
  {
    id: bigserial("id", { mode: "number" }).primaryKey(),
    dealerMarginPaise: bigint("dealer_margin_paise", { mode: "number" }).notNull(),
    nearBestWindowPct: numeric("near_best_window_pct", { precision: 5, scale: 2 })
      .default("25")
      .notNull(),
    expectedEmiFilterRequired: boolean("expected_emi_filter_required").default(false).notNull(),
    upfrontFilterRequired: boolean("upfront_filter_required").default(false).notNull(),
    disclaimerText: text("disclaimer_text").notNull(),
    cardFooterDisclaimer: text("card_footer_disclaimer").notNull(),
    contactPhone: text("contact_phone").notNull(),
    contactEmail: text("contact_email").notNull(),
    contactWhatsapp: text("contact_whatsapp").notNull(),
    validFrom: timestamp("valid_from", { withTimezone: true }).defaultNow().notNull(),
    validTo: timestamp("valid_to", { withTimezone: true }),
    configVersionId: bigint("config_version_id", { mode: "number" })
      .references(() => calcConfigVersions.id)
      .notNull(),
  },
  (t) => ({
    currentIdx: index("calc_settings_valid_to_idx").on(t.validTo),
  }),
);

export const calcBatteryModels = pgTable(
  "calc_battery_models",
  {
    id: serial("id").primaryKey(),
    skuCode: text("sku_code").notNull(),
    displayName: text("display_name").notNull(),
    voltage: numeric("voltage", { precision: 5, scale: 1 }),
    capacityAh: integer("capacity_ah"),
    chargerSku: text("charger_sku"),
    status: calcRecordStatus("status").default("active").notNull(),
  },
  (t) => ({
    skuUq: uniqueIndex("calc_battery_models_sku_uq").on(t.skuCode),
  }),
);

// price_with_gst = (battery+harness+soc+iot)*1.18 + charger*1.05 (per-component gst stored).
export const calcComponentPrices = pgTable(
  "calc_component_prices",
  {
    id: bigserial("id", { mode: "number" }).primaryKey(),
    modelId: integer("model_id")
      .references(() => calcBatteryModels.id)
      .notNull(),
    component: calcComponentKind("component").notNull(),
    amountPaise: bigint("amount_paise", { mode: "number" }).notNull(),
    gstMultiplier: numeric("gst_multiplier", { precision: 5, scale: 4 }).notNull(),
    validFrom: timestamp("valid_from", { withTimezone: true }).defaultNow().notNull(),
    validTo: timestamp("valid_to", { withTimezone: true }),
    configVersionId: bigint("config_version_id", { mode: "number" })
      .references(() => calcConfigVersions.id)
      .notNull(),
  },
  (t) => ({
    lookupIdx: index("calc_component_prices_lookup_idx").on(t.modelId, t.component, t.validTo),
  }),
);

// Optional per-model dealer-margin override. Precedence: model override -> settings.
export const calcDealerMarginOverrides = pgTable(
  "calc_dealer_margin_overrides",
  {
    id: bigserial("id", { mode: "number" }).primaryKey(),
    modelId: integer("model_id")
      .references(() => calcBatteryModels.id)
      .notNull(),
    dealerMarginPaise: bigint("dealer_margin_paise", { mode: "number" }).notNull(),
    validFrom: timestamp("valid_from", { withTimezone: true }).defaultNow().notNull(),
    validTo: timestamp("valid_to", { withTimezone: true }),
    configVersionId: bigint("config_version_id", { mode: "number" })
      .references(() => calcConfigVersions.id)
      .notNull(),
  },
  (t) => ({
    lookupIdx: index("calc_dealer_margin_overrides_lookup_idx").on(t.modelId, t.validTo),
  }),
);

// Variant A: flatMaxLoan + flatInterestRate used. Variant B: those are null; cap is
// per-model (calc_nbfc_model_caps), rate is per-scheme (calc_schemes).
export const calcNbfcs = pgTable(
  "calc_nbfcs",
  {
    id: serial("id").primaryKey(),
    nbfcCode: text("nbfc_code").notNull(),
    name: text("name").notNull(),
    variant: calcEngineVariant("variant").notNull(),
    maxLoanCapPaise: bigint("max_loan_cap_paise", { mode: "number" }),
    flatInterestRate: numeric("flat_interest_rate", { precision: 10, scale: 7 }),
    fileFeePaise: bigint("file_fee_paise", { mode: "number" }).notNull(),
    defaultProcessingFeePaise: bigint("default_processing_fee_paise", {
      mode: "number",
    }).notNull(),
    status: calcRecordStatus("status").default("active").notNull(),
    validFrom: timestamp("valid_from", { withTimezone: true }).defaultNow().notNull(),
    validTo: timestamp("valid_to", { withTimezone: true }),
    configVersionId: bigint("config_version_id", { mode: "number" })
      .references(() => calcConfigVersions.id)
      .notNull(),
  },
  (t) => ({
    nameUq: uniqueIndex("calc_nbfcs_name_uq").on(t.name, t.validTo),
    statusIdx: index("calc_nbfcs_status_idx").on(t.status, t.validTo),
  }),
);

export const calcNbfcModelCaps = pgTable(
  "calc_nbfc_model_caps",
  {
    id: bigserial("id", { mode: "number" }).primaryKey(),
    nbfcId: integer("nbfc_id")
      .references(() => calcNbfcs.id)
      .notNull(),
    modelId: integer("model_id")
      .references(() => calcBatteryModels.id)
      .notNull(),
    maxLoanCapPaise: bigint("max_loan_cap_paise", { mode: "number" }).notNull(),
    validFrom: timestamp("valid_from", { withTimezone: true }).defaultNow().notNull(),
    validTo: timestamp("valid_to", { withTimezone: true }),
    configVersionId: bigint("config_version_id", { mode: "number" })
      .references(() => calcConfigVersions.id)
      .notNull(),
  },
  (t) => ({
    lookupIdx: index("calc_nbfc_model_caps_lookup_idx").on(t.nbfcId, t.modelId, t.validTo),
  }),
);

// code "XbyY" derived from (tenure, advance). appliedInterestRate = the rate actually
// used in interest = loan*rate*tenure/12 (NOT a display/MBD rate). advance < tenure.
export const calcSchemes = pgTable(
  "calc_schemes",
  {
    id: bigserial("id", { mode: "number" }).primaryKey(),
    nbfcId: integer("nbfc_id")
      .references(() => calcNbfcs.id)
      .notNull(),
    tenureMonths: integer("tenure_months").notNull(),
    advanceMonths: integer("advance_months").notNull(),
    code: text("code").notNull(),
    appliedInterestRate: numeric("applied_interest_rate", { precision: 10, scale: 7 }),
    processingFeePaise: bigint("processing_fee_paise", { mode: "number" }),
    advanceInterestRate: numeric("advance_interest_rate", { precision: 10, scale: 7 }),
    status: calcRecordStatus("status").default("active").notNull(),
    validFrom: timestamp("valid_from", { withTimezone: true }).defaultNow().notNull(),
    validTo: timestamp("valid_to", { withTimezone: true }),
    configVersionId: bigint("config_version_id", { mode: "number" })
      .references(() => calcConfigVersions.id)
      .notNull(),
  },
  (t) => ({
    nbfcIdx: index("calc_schemes_nbfc_idx").on(t.nbfcId, t.status, t.validTo),
    codeIdx: index("calc_schemes_code_idx").on(t.nbfcId, t.code),
  }),
);

// An NBFC is either PAN_INDIA (city_normalized NULL) or has explicit CITY rows.
// A city may map to multiple NBFCs (intended).
export const calcNbfcCoverage = pgTable(
  "calc_nbfc_coverage",
  {
    id: bigserial("id", { mode: "number" }).primaryKey(),
    nbfcId: integer("nbfc_id")
      .references(() => calcNbfcs.id)
      .notNull(),
    coverageType: calcCoverageType("coverage_type").notNull(),
    cityNormalized: text("city_normalized"),
    stateCode: text("state_code"),
    cityDisplay: text("city_display"),
    validFrom: timestamp("valid_from", { withTimezone: true }).defaultNow().notNull(),
    validTo: timestamp("valid_to", { withTimezone: true }),
    configVersionId: bigint("config_version_id", { mode: "number" })
      .references(() => calcConfigVersions.id)
      .notNull(),
  },
  (t) => ({
    cityIdx: index("calc_nbfc_coverage_city_idx").on(t.cityNormalized, t.validTo),
    nbfcIdx: index("calc_nbfc_coverage_nbfc_idx").on(t.nbfcId, t.validTo),
  }),
);

// Saved quotes — one row per calculation. Website leads have dealer_id NULL
// (that is how public/website leads are distinguished from dealer-portal ones).
// otp_verification_id references the CRM-only calc_otp_verifications table; the
// website never writes it, so the FK is intentionally NOT declared here.
export const calcLeads = pgTable(
  "calc_leads",
  {
    id: uuid("id").defaultRandom().primaryKey(),
    createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
    dealerId: varchar("dealer_id", { length: 255 }),
    customerName: text("customer_name").notNull(),
    phone: text("phone").notNull(),
    pincode: text("pincode"),
    city: text("city"),
    state: text("state"),
    expectedEmiPaise: bigint("expected_emi_paise", { mode: "number" }),
    upfrontAbilityPaise: bigint("upfront_ability_paise", { mode: "number" }),
    tenureMonths: integer("tenure_months"),
    modelId: integer("model_id").references(() => calcBatteryModels.id),
    filterOutcome: calcLeadFilterOutcome("filter_outcome"),
    configVersionId: bigint("config_version_id", { mode: "number" }).references(
      () => calcConfigVersions.id,
    ),
    resultSnapshot: jsonb("result_snapshot"),
    crmLeadId: text("crm_lead_id"),
    crmSyncedAt: timestamp("crm_synced_at", { withTimezone: true }),
    idempotencyKey: text("idempotency_key"),
    otpVerificationId: uuid("otp_verification_id"),
    otpVerifiedAt: timestamp("otp_verified_at", { withTimezone: true }),
    waResultsStatus: text("wa_results_status"),
    waResultsSentAt: timestamp("wa_results_sent_at", { withTimezone: true }),
  },
  (t) => ({
    phoneIdx: index("calc_leads_phone_idx").on(t.phone),
    createdAtIdx: index("calc_leads_created_at_idx").on(t.createdAt),
    dealerIdx: index("calc_leads_dealer_idx").on(t.dealerId),
  }),
);
