/**
 * Scrape Trontek product specifications from trontek.com
 *
 * Usage:
 *   npx tsx scripts/scrape-trontek.ts
 *
 * Prerequisites:
 *   - FIRECRAWL_API_KEY set in .env
 *
 * Output:
 *   - docs/trontek-products.md
 */

import "dotenv/config";
import { writeFileSync, mkdirSync } from "fs";
import { join } from "path";
import {
  scrapeWithPrompt,
  mapSite,
} from "../src/lib/firecrawl";

// ---------------------------------------------------------------------------
// Config
// ---------------------------------------------------------------------------

const SEED_URLS = {
  battery: "https://trontek.com/products/e-rickshaw-lithium-battery/",
  inverter: "https://trontek.com/products/lithium-inverter-battery-home/",
  charger: "https://trontek.com/product/ev-charger",
};

const DELAY_MS = 2500; // between Firecrawl calls

// ---------------------------------------------------------------------------
// Extraction prompts
// ---------------------------------------------------------------------------

const BATTERY_PROMPT = `Extract ALL e-rickshaw / 3-wheeler lithium battery product variants listed on this page.
For EACH variant return a JSON object with these fields (use null if not available):
- variantName (string, e.g. "51V 105AH")
- nominalVoltage (string)
- ratedCapacity (string)
- energy (string, in kWh)
- cellChemistry (string)
- chargingVoltage (string)
- chargingCurrent (string)
- dischargeCurrent (string)
- peakDischargeCurrent (string)
- cutoffVoltage (string)
- dimensions (string)
- weight (string)
- casingMaterial (string)
- ipRating (string)
- chargingTempRange (string)
- dischargingTempRange (string)
- cycleLife (string)
- chargingTime (string)
- rangePerCharge (string)
- batteryLifespan (string)
- warranty (string)
- price (string)
- certifications (string[])
- safetyFeatures (string[])

Return a JSON array of objects — one per variant. Include ALL variants visible on the page.`;

const INVERTER_PROMPT = `Extract ALL lithium inverter battery product variants from this page.
For EACH variant return a JSON object with these fields (use null if not available):
- variantName (string, e.g. "Powercube 1.4+")
- nominalVoltage (string)
- ratedCapacity (string)
- energy (string, in kWh)
- cellChemistry (string)
- chargingVoltage (string)
- chargingCurrent (string)
- dischargeCurrent (string)
- dimensions (string)
- weight (string)
- cycleLife (string)
- chargingTime (string)
- backupTime (string)
- roundTripEfficiency (string)
- batteryLifespan (string)
- warranty (string)
- price (string)
- certifications (string[])
- safetyFeatures (string[])
- bmsFeatures (string[])

Return a JSON array of objects — one per variant.`;

const CHARGER_PROMPT = `Extract ALL EV charger product variants from this page.
For EACH variant return a JSON object with these fields (use null if not available):
- modelNumber (string, e.g. "TK-500")
- wattage (string)
- inputVoltage (string)
- outputVoltage (string)
- outputCurrent (string)
- efficiency (string)
- chargingTime (string)
- dimensions (string)
- weight (string)
- casingMaterial (string)
- ipRating (string)
- protections (string[])
- compatibility (string[])
- warranty (string)
- price (string)
- certifications (string[])

Return a JSON array of objects — one per variant.`;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function sleep(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}

async function scrapeCategory(url: string, prompt: string, label: string) {
  console.log(`\n🔍 Scraping ${label} from ${url} ...`);
  try {
    const result = await scrapeWithPrompt(url, prompt);
    console.log(`   ✅ Got response for ${label}`);
    return result;
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    console.error(`   ❌ Failed to scrape ${label}: ${msg}`);
    return null;
  }
}

function toMarkdownTable(items: Record<string, unknown>[], title: string): string {
  if (!items || items.length === 0) return `### ${title}\n\n_No data extracted._\n`;

  let md = "";
  for (const item of items) {
    const name =
      (item.variantName as string) ||
      (item.modelNumber as string) ||
      "Unknown Variant";
    md += `### ${name}\n\n`;
    md += `| Specification | Value |\n`;
    md += `|---|---|\n`;
    for (const [key, val] of Object.entries(item)) {
      if (key === "variantName" || key === "modelNumber") continue;
      const display = Array.isArray(val)
        ? val.join(", ")
        : val === null || val === undefined
          ? "_not available_"
          : String(val);
      md += `| ${formatKey(key)} | ${display} |\n`;
    }
    md += "\n";
  }
  return md;
}

function formatKey(key: string): string {
  return key
    .replace(/([A-Z])/g, " $1")
    .replace(/^./, (s) => s.toUpperCase())
    .trim();
}

function extractJson(result: { json?: unknown; markdown?: string } | null): Record<string, unknown>[] {
  if (!result) return [];

  // Try the structured JSON first
  const jsonData = (result as Record<string, unknown>).json;
  if (jsonData) {
    if (Array.isArray(jsonData)) return jsonData as Record<string, unknown>[];
    if (typeof jsonData === "object" && jsonData !== null) {
      // Sometimes Firecrawl wraps in an object with a data/products/items key
      for (const key of ["data", "products", "items", "variants", "results"]) {
        const nested = (jsonData as Record<string, unknown>)[key];
        if (Array.isArray(nested)) return nested as Record<string, unknown>[];
      }
      return [jsonData as Record<string, unknown>];
    }
  }

  // Try parsing from markdown if JSON extraction failed
  const markdown = (result as Record<string, unknown>).markdown;
  if (typeof markdown === "string") {
    const jsonMatch = markdown.match(/```json\s*([\s\S]*?)```/);
    if (jsonMatch) {
      try {
        const parsed = JSON.parse(jsonMatch[1]);
        if (Array.isArray(parsed)) return parsed;
        return [parsed];
      } catch { /* ignore parse errors */ }
    }
  }

  return [];
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function main() {
  if (!process.env.FIRECRAWL_API_KEY || process.env.FIRECRAWL_API_KEY === "[TO_BE_PROVIDED]") {
    console.error("❌ FIRECRAWL_API_KEY is not set in .env");
    process.exit(1);
  }

  const today = new Date().toISOString().slice(0, 10);

  // Step 1: Discover URLs (optional, for logging)
  console.log("📡 Mapping trontek.com site...");
  try {
    const siteMap = await mapSite("https://trontek.com");
    const links = (siteMap as Record<string, unknown>)?.links;
    if (Array.isArray(links)) {
      console.log(`   Found ${links.length} URLs on trontek.com`);
      const productLinks = links.filter((l: unknown) => {
        const url = typeof l === "string" ? l : (l as Record<string, unknown>)?.url;
        return typeof url === "string" && /\/products?\//.test(url);
      });
      console.log(`   ${productLinks.length} are product-related`);
    }
  } catch (err) {
    console.warn("   ⚠️  Site map failed, continuing with seed URLs...");
  }

  await sleep(DELAY_MS);

  // Step 2: Scrape each category
  const batteryResult = await scrapeCategory(SEED_URLS.battery, BATTERY_PROMPT, "E-Rickshaw Batteries");
  await sleep(DELAY_MS);

  const inverterResult = await scrapeCategory(SEED_URLS.inverter, INVERTER_PROMPT, "Inverter Batteries");
  await sleep(DELAY_MS);

  const chargerResult = await scrapeCategory(SEED_URLS.charger, CHARGER_PROMPT, "EV Chargers");

  // Step 3: Extract JSON from results
  const batteries = extractJson(batteryResult);
  const inverters = extractJson(inverterResult);
  const chargers = extractJson(chargerResult);

  console.log(`\n📊 Extracted: ${batteries.length} batteries, ${inverters.length} inverters, ${chargers.length} chargers`);

  // Step 4: Build markdown
  let md = `# Trontek Product Specifications\n\n`;
  md += `> Scraped on ${today} from [trontek.com](https://trontek.com)\n\n`;
  md += `---\n\n`;

  md += `## E-Rickshaw Lithium Batteries\n\n`;
  md += `_Source: ${SEED_URLS.battery}_\n\n`;
  md += toMarkdownTable(batteries, "Batteries");

  md += `---\n\n`;

  md += `## Inverter Batteries\n\n`;
  md += `_Source: ${SEED_URLS.inverter}_\n\n`;
  md += toMarkdownTable(inverters, "Inverters");

  md += `---\n\n`;

  md += `## EV Chargers\n\n`;
  md += `_Source: ${SEED_URLS.charger}_\n\n`;
  md += toMarkdownTable(chargers, "Chargers");

  // Also append raw markdown from pages if available
  md += `---\n\n## Raw Page Content\n\n`;
  md += `<details>\n<summary>Battery page markdown</summary>\n\n`;
  md += (batteryResult as Record<string, unknown>)?.markdown || "_No markdown captured_";
  md += `\n\n</details>\n\n`;
  md += `<details>\n<summary>Inverter page markdown</summary>\n\n`;
  md += (inverterResult as Record<string, unknown>)?.markdown || "_No markdown captured_";
  md += `\n\n</details>\n\n`;
  md += `<details>\n<summary>Charger page markdown</summary>\n\n`;
  md += (chargerResult as Record<string, unknown>)?.markdown || "_No markdown captured_";
  md += `\n\n</details>\n`;

  // Step 5: Write output
  const outDir = join(process.cwd(), "docs");
  mkdirSync(outDir, { recursive: true });
  const outPath = join(outDir, "trontek-products.md");
  writeFileSync(outPath, md, "utf-8");
  console.log(`\n✅ Written to ${outPath}`);
}

// ---------------------------------------------------------------------------
// Supplementary scraping from Amazon/IndiaMART for missing specs
// ---------------------------------------------------------------------------

const SUPPLEMENT_URLS = [
  // Amazon Trontek battery listings
  "https://www.amazon.in/stores/Trontek/page/E3AE9F8D-5BBA-4E5E-95F3-06E271B6FC8E",
  // IndiaMART Trontek listings
  "https://www.indiamart.com/tronetek/lithium-ion-battery.html",
];

const SUPPLEMENT_PROMPT = `Extract ALL product specifications for Trontek lithium batteries, inverters, and chargers listed on this page.
For EACH product, extract a JSON object with:
- productName (string)
- category (string: "battery", "inverter", or "charger")
- voltage (string)
- capacity (string)
- energy (string)
- weight (string)
- dimensions (string)
- cycleLife (string)
- chargingTime (string)
- warranty (string)
- price (string)
- operatingTemp (string)
- ipRating (string)
- certifications (string[])
- allSpecs (object with any other specification key-value pairs found)

Return a JSON array of all products found.`;

async function supplementScrape() {
  console.log("\n📡 Supplementing from Amazon/IndiaMART...");

  const allSupplemental: Record<string, unknown>[] = [];

  for (const url of SUPPLEMENT_URLS) {
    await sleep(DELAY_MS);
    try {
      console.log(`\n🔍 Scraping ${url} ...`);
      const result = await scrapeWithPrompt(url, SUPPLEMENT_PROMPT);
      console.log(`   ✅ Got response`);
      const items = extractJson(result);
      console.log(`   Found ${items.length} products`);
      // Tag each item with source
      for (const item of items) {
        item._source = url.includes("amazon") ? "Amazon" : "IndiaMART";
        item._sourceUrl = url;
      }
      allSupplemental.push(...items);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      console.warn(`   ⚠️  Failed: ${msg}`);
    }
  }

  return allSupplemental;
}

async function mainWithSupplement() {
  await main();

  const supplemental = await supplementScrape();

  if (supplemental.length > 0) {
    console.log(`\n📊 Got ${supplemental.length} supplemental products`);

    // Append supplemental data to the markdown file
    const outPath = join(process.cwd(), "docs", "trontek-products.md");
    let extra = `\n\n---\n\n## Supplemental Data (Amazon / IndiaMART)\n\n`;
    extra += `> These specs come from third-party listings and may provide details missing from the official site.\n\n`;

    for (const item of supplemental) {
      const name = (item.productName as string) || "Unknown Product";
      const source = item._source as string;
      extra += `### ${name} _(${source})_\n\n`;
      extra += `| Specification | Value |\n`;
      extra += `|---|---|\n`;
      for (const [key, val] of Object.entries(item)) {
        if (key.startsWith("_")) continue;
        if (key === "productName") continue;
        if (typeof val === "object" && val !== null && !Array.isArray(val)) {
          // Expand nested allSpecs object
          for (const [sk, sv] of Object.entries(val as Record<string, unknown>)) {
            extra += `| ${formatKey(sk)} | ${sv ?? "_not available_"} |\n`;
          }
        } else {
          const display = Array.isArray(val)
            ? val.join(", ")
            : val === null || val === undefined
              ? "_not available_"
              : String(val);
          extra += `| ${formatKey(key)} | ${display} |\n`;
        }
      }
      extra += "\n";
    }

    const { readFileSync } = await import("fs");
    const existing = readFileSync(outPath, "utf-8");
    writeFileSync(outPath, existing + extra, "utf-8");
    console.log(`✅ Appended supplemental data to ${outPath}`);
  } else {
    console.log("\n⚠️  No supplemental data found");
  }
}

mainWithSupplement().catch((err) => {
  console.error("Fatal error:", err);
  process.exit(1);
});
