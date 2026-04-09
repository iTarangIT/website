# Trontek Navigation & Product Flow Deep Analysis

> Detailed UI/UX flow analysis for iTarang competitive research.
> Scraped and analyzed on 2026-04-08 using Firecrawl.
> **Scope:** 3W lithium batteries, inverters, and chargers ONLY.
> **No copyrighted content copied verbatim.**

---

## Source URLs Analyzed

| # | URL | Type | Method |
|---|-----|------|--------|
| 1 | `https://trontek.com/` | Homepage | scrape + map |
| 2 | `https://trontek.com/products/e-rickshaw-lithium-battery/` | 3W Battery page | scrape + extract |
| 3 | `https://trontek.com/products/lithium-inverter-battery-home/` | Inverter Battery page | scrape + extract |
| 4 | `https://trontek.com/products/tk500-w-series` | TK-500 Charger | scrape + extract |
| 5 | `https://trontek.com/products/tk840-w-series` | TK-840 Charger | scrape |
| 6 | `https://trontek.com/products/tk1350-w-series` | TK-1350 Charger | scrape |
| 7 | `https://trontek.com/products/tk2000-w-series` | TK-2000 Charger | scrape |
| 8 | `https://trontek.com/products/tk3000-w-series` | TK-3000 Charger | scrape |
| 9 | `https://www.amazon.in/.../B0G1N7BXP8` | Amazon 51V 132AH listing | scrape |
| 10 | `https://www.amazon.in/.../B0G1HSQ3B9` | Amazon TK-500 listing | scrape |
| 11 | `https://www.energetica-india.net/...powercube...` | Powercube press article | scrape |
| 12 | `https://www.ess-news.com/.../trontek...` | Powercube ESS News article | scrape |
| 13 | `https://www.indiamart.com/.../2858000540855.html` | IndiaMART battery listing | scrape |
| 14 | `https://trontek.com/blog/complete-guide-to-e-rickshaw-lithium-batteries-in-india/` | Blog guide | scrape |

---

## PART 1: Navigation & Dropdown Analysis

### 1.1 Products Button / Menu Interaction

**What Firecrawl reveals about the header navigation:**

The Trontek website is WordPress-based (WordPress 6.9.4). The navigation menu is rendered via JavaScript/WordPress theme, so the dropdown DOM is **not fully visible** in the Firecrawl markdown extraction. However, from the homepage content structure and sitemap mapping, we can reconstruct the full navigation:

**Navigation type:** Desktop mega-menu / dropdown (JavaScript-rendered)
**Interaction type:** Likely hover-triggered on desktop (standard WordPress dropdown pattern). Click on mobile.
**Sticky header:** Yes (standard WordPress behavior with "Enquire Now" CTA)

### 1.2 What Is Shown Inside the Products Dropdown

Based on sitemap discovery and homepage product grid, the Products menu contains these categories:

| Category | Destination URL | Relevant? |
|----------|----------------|-----------|
| E-Rickshaw Lithium Battery | `/products/e-rickshaw-lithium-battery/` | YES |
| Electric Scooter Battery | `/products/electric-scooter-battery/` | No |
| Lithium Inverter Battery (Home) | `/products/lithium-inverter-battery-home/` | YES |
| Golf Cart Battery | `/products/golf-cart/` | No |
| Solid State / LMNC | `/products/solid-state/` and `/products/lmnc/` | No |
| MHE Batteries | `/products/mhe/` | No |
| Industrial BESS | `/products/industrial-bess/` | No |
| Solar Street Light | `/products/solar-street-light-storage/` | No |
| Snap Fit | `/products/snap-fit/` | No |
| EV Chargers (TK series) | `/products/tk500-w-series/` etc. | YES |
| Hybrid Inverters | `/single-phase-inverter`, `/three-phase-light`, `/three-phase-heavy` | Partially relevant |
| Solar GTI | `/products/solar-gti/` | No |
| Small Office | `/products/small-office/` | No |
| Industrial Power Cube | `/products/industrial-power-cube/` | No |

**Visual arrangement:** Based on the homepage product carousel, products are shown as cards with:
- Product image (centered product shot)
- Category name in bold caps (e.g., "LITHIUM-ION E-Rickshaw BATTERIES")
- Short description (1 line)
- "View More" CTA link
- "NEW" badge on some items (Hybrid Inverter, GTI Inverter)

**Layout:** The homepage shows products in a horizontal carousel/slider (repeating items visible in scrape). The nav dropdown likely uses a simpler list or multi-column layout.

### 1.3 Dropdown Structure (Reconstructed)

```
Products (nav item)
  |
  |-- E-Rickshaw Lithium Battery     → /products/e-rickshaw-lithium-battery/
  |-- Electric Scooter Battery       → /products/electric-scooter-battery/
  |-- Lithium Inverter Battery       → /products/lithium-inverter-battery-home/
  |-- Golf Cart Battery              → /products/golf-cart/
  |-- Drones / Solid State / LMNC    → /products/solid-state/ or /products/lmnc/
  |-- MHE Batteries                  → /products/mhe/
  |-- Industrial BESS                → /products/industrial-bess/
  |-- Solar Street Light             → /products/solar-street-light-storage/
  |-- EV Chargers                    → /products/tk500-w-series/ (default charger entry)
  |-- Hybrid Inverters               → /single-phase-inverter (NOT under /products/)
  |-- Solar GTI                      → /products/solar-gti/
  |-- Small Office                   → /products/small-office/
  |-- Industrial Power Cube          → /products/industrial-power-cube/
  |-- Snap Fit                       → /products/snap-fit/
```

**Important observation:** The `/products/` page itself (`https://trontek.com/products`) exists but has minimal content — Trontek does NOT have a products grid/listing page. Each category goes directly to its own long-form detail page.

### 1.4 Homepage Product Carousel Items

The homepage shows a product carousel with these cards (in order as scraped):

1. **HYBRID INVERTER** (NEW) → `/single-phase-inverter`
2. **GOLF CART BATTERY** → `/golf-cart`
3. **Drones** → `/solid-state`
4. **EV Charger** → `/tk500-w-series`
5. **GTI INVERTER** (NEW) → `/solar-gti`
6. **LITHIUM-ION E-Rickshaw BATTERIES** → `/3-wheeler`
7. **TWO WHEELER** → `/2-wheeler`

**Note:** The homepage carousel links to `/3-wheeler` (not `/products/e-rickshaw-lithium-battery/`). This suggests `/3-wheeler` may be an alias or different page. However, the sitemap shows the canonical product page at `/products/e-rickshaw-lithium-battery/`.

### 1.5 Click Flow for Relevant Categories

#### When user clicks "E-Rickshaw Lithium Battery"
- **From nav dropdown:** Goes to `/products/e-rickshaw-lithium-battery/`
- **From homepage carousel:** Goes to `/3-wheeler` (possibly a redirect or alias)
- **Destination:** Single long-form page with all 11 variants on ONE page
- **Page title:** "E Rickshaw Lithium Battery | Price & Specifications in India"

#### When user clicks "Lithium Inverter Battery"
- **From nav dropdown:** Goes to `/products/lithium-inverter-battery-home/`
- **Destination:** Single page with 2 variants (Powercube 1.4+ and 2.7+)
- **Page title:** "Lithium Ion Battery for Inverter | Home Inverter Battery | Trontek"

#### When user clicks "EV Charger"
- **From nav/homepage:** Goes to `/products/tk500-w-series`
- **Destination:** Individual charger model page (TK-500 only)
- **Other charger models are separate pages** — no charger index page exists
- **Page titles:** "TK500 W-Series - Trontek", "TK840 W-Series - Trontek", etc.

### 1.6 Mobile Behavior (Inferred)

- WordPress responsive theme with `viewport` meta tag set
- Navigation likely collapses to hamburger menu on mobile
- Product pages use full-width single-column layout (responsive-friendly)
- No mobile-specific UI patterns detected from scrape

---

## PART 2: Page Flow Analysis — Per Category

### 2.1 E-Rickshaw Lithium Battery Page

**URL:** `https://trontek.com/products/e-rickshaw-lithium-battery/`
**Default variant shown:** 51V 132AH (6.758kWh) — appears first in the page content

#### Section-by-Section Flow (Top to Bottom)

```
1. HERO BANNER IMAGE
   - Full-width banner (single-pd-1.jpg)
   - Lifestyle/product shot
   - No text overlay visible in scrape

2. VARIANT SELECTOR (Tab Strip)
   - Horizontal list of clickable variant buttons
   - 11 variants across 4 voltage levels:
     • 51V: 105AH, 132AH, 153AH, 232AH
     • 61V: 105AH, 132AH, 153AH, 232AH
     • 64V: 105AH, 132AH
     • 72V: 232AH
   - Clicking a variant changes the content below WITHOUT page reload

3. PRODUCT TITLE + CAPACITY BADGE
   - "E Rickshaw Lithium Battery"
   - Sub: "51V 132AH (6.758kWh)"

4. PRODUCT IMAGE
   - Centered isolated product photo (e.g., "51V 132AH.png")
   - One image per variant
   - White/neutral background
   - Single angle only

5. PRODUCT DESCRIPTION
   - 1 paragraph, benefit-focused
   - Mentions: LiFePO4, kWh, driving range, charging speed, durability
   - Tailored per variant (higher capacity = more emphasis on range/heavy-duty)
   - SEO keyword-heavy

6. "SAFETY FEATURES" LABEL
   - Decorative text ("Safety Features")

7. SAFETY FEATURES SECTION (Icon Grid)
   - Heading: "Advanced Safety Features of Trontek E Rickshaw Lithium Battery"
   - 4 icons in a grid:
     a. Over-charge / Over-discharge — smart protection prevents overcharge/deep discharge
     b. Short Circuit — withstands short circuit without fire/explosion
     c. Acupuncture — handles nail puncture test without thermal runaway
     d. Thermal Shock — withstands sudden temperature changes
   - IDENTICAL text for ALL variants

8. "WHY CHOOSE TRONTEK" SECTION
   - Dual-column bullet list (10 items total):
     Left column:
       • Attractive cycle life
       • Extended safety performance
       • Wide operating temperature range
       • Unrivalled high temperature performance
       • Green energy without metal contaminant
     Right column:
       • High capacity
       • Steady output voltage
       • Little self-discharge
       • Double safety protection
       • Withstanding very high level of vibrations and shocks
   - IDENTICAL text for ALL variants

9. PRODUCT SPECIFICATIONS
   - **IMAGE-BASED (not HTML)**
   - Each variant has a different .jpg spec image:
     • 51v-132ah-product.jpg
     • 51v-105ah-product.jpg
     • 51v-232ah-product.jpg
     • 61V-105Ah-product.jpg
     • 61V-132Ah-product.jpg
     • 61v-153ah-product.jpg
     • 61v-232ah-product.jpg
     • 64v-105ah-product.jpg
     • 64v-132ah-product.jpg
     • 73v-232ah-product.jpg (note: URL says 73v, product is 72V)
   - Specs visible in images (cannot be extracted as text):
     voltage, capacity, energy, dimensions, weight, cycle life,
     charging specs, operating temperature, certifications

--- SECTIONS 3-9 REPEAT FOR EACH OF THE 11 VARIANTS ---

10. FAQ SECTION (appears once at bottom)
    - "Everything you need to know about Trontek E-Rickshaw Lithium Batteries"
    - 3 questions (accordion):
      a. "What is the price of e rickshaw lithium battery in India?"
         → starts from 55,000 INR
      b. "Why is lithium battery better for e rickshaw?"
         → longer lifespan, lightweight, fast charging, improved range
      c. "How long does an e rickshaw lithium battery last?"
         → 3 to 6 years depending on usage
```

#### Interaction Patterns

- **Variant switching:** Tab-style buttons at top, no page reload
- **Content changes:** Product image, title/capacity, description, spec image ALL change per variant
- **Static sections:** Safety features and "Why Choose" text remain IDENTICAL across all variants
- **Default variant:** 51V 132AH appears to be the default (shown first)
- **No breadcrumbs** visible
- **No related products section**
- **No CTA section at bottom** (only FAQ, then footer)

---

### 2.2 Inverter Battery Page (Powercube)

**URL:** `https://trontek.com/products/lithium-inverter-battery-home/`

#### Section-by-Section Flow

```
1. HERO BANNER IMAGE
   - Full-width banner (Home-internal-banner.jpg)
   - Home/lifestyle context

2. PAGE TITLE
   - "Lithium Ion Battery for Inverter"
   - Sub: "Powercube 1.4+ | Powercube 2.7+"
   - NOTE: No tab-based variant selector visible — both variants shown as subtitle

3. PRODUCT IMAGE
   - Single product image (home-product.png)
   - Shows the Powercube unit

4. PRODUCT DESCRIPTION
   - 1 paragraph about reliable power backup, faster charging, longer lifespan
   - Mentions: advanced lithium technology, BMS, compact design

5. SAFETY FEATURES SECTION (Icon Grid)
   - "Advanced Features of Trontek Lithium Ion Battery for Inverter"
   - 4 feature icons (DIFFERENT from battery page):
     a. Smart Control System — monitors charging status, battery health
     b. High Safety — prevents overcharging, overheating, short circuits
     c. Long Life Battery — thousands of charge cycles
     d. Advanced BMS Protection — monitors voltage, temperature, charging

6. "BEST INVERTER BATTERY FOR HOME" SECTION
   - Informational paragraph about choosing inverter batteries
   - Mentions: backup time, charging speed, battery life
   - No bullet list format (unlike battery page)

7. PRODUCT SPECIFICATIONS
   - **IMAGE-BASED (not HTML)**
   - Single image for both variants: "Home (TK12100 TK25100).jpg"
   - Model names visible: TK12100 (Powercube 1.4+) and TK25100 (Powercube 2.7+)

8. FAQ SECTION (4 questions, accordion)
   a. "What is a lithium ion battery for inverter?"
      → rechargeable battery for inverter systems
   b. "What is the inverter battery price in India?"
      → starts from Rs. 20,000
   c. "Which is the best inverter battery for home?"
      → lithium due to longer life, faster charging, higher efficiency
   d. "How long does a lithium inverter battery last?"
      → 8 to 10 years
```

#### Key Differences from Battery Page

- **NO variant tab selector** — both Powercube variants shown together
- **Single spec image** covers both variants side-by-side
- **Different safety icons** (Smart Control, High Safety, Long Life, BMS vs. Overcharge, Short Circuit, Acupuncture, Thermal)
- **No "Why Choose" dual-column section** — replaced with "Best Inverter Battery for Home" paragraph
- **Shorter page** — only 2 variants vs. 11
- **No variant switching interaction** — static single page

---

### 2.3 Charger Pages (TK W-Series)

**URLs:** 5 separate pages, one per charger model

| Model | URL | Wattage (from name) |
|-------|-----|---------------------|
| TK-500 W-Series | `/products/tk500-w-series` | 500W |
| TK-840 W-Series | `/products/tk840-w-series` | 840W |
| TK-1350 W-Series | `/products/tk1350-w-series` | 1350W |
| TK-2000 W-Series | `/products/tk2000-w-series` | 2000W |
| TK-3000 W-Series | `/products/tk3000-w-series` | 3000W |

#### Section-by-Section Flow (ALL 5 charger pages have identical structure)

```
1. HERO BANNER IMAGE
   - Same banner for all chargers (single-banner-2.jpg)

2. PAGE TITLE
   - "EV CHARGER"
   - Sub: "TK-[XXX] W-SERIES"

3. PRODUCT IMAGE
   - Individual charger product shot per model
   - Images: TK500W.png, TK840W.png, TK1350W.png, TK2000W.png, TK3000W.png

4. PRODUCT DESCRIPTION
   - IDENTICAL text for ALL 5 charger pages:
     "Our extensive product line of chargers covers multiple
      applications across various verticals. It comes with a
      hermetic and durable seal structure to provide a
      hassle-free charging experience. All our units are
      pre-tested for their efficiency, stability, reliability and
      protection."

5. PRODUCT SPECIFICATIONS
   - **IMAGE-BASED (not HTML)**
   - Individual spec image per model:
     Tk-500.jpg, Tk-840.jpg, Tk-1350.jpg, Tk-2000.jpg, Tk-3000.jpg

--- END OF PAGE ---
```

#### Key Observations About Charger Pages

- **Extremely thin pages** — only 5 sections, no safety grid, no FAQ, no "Why Choose"
- **Identical description** across all 5 models — zero differentiation
- **No variant switching** — each charger is its own standalone page
- **No breadcrumbs, no CTA, no FAQ, no trust sections**
- **No charger index/listing page** — user must know which model to visit
- **Specs are entirely image-locked** — cannot be extracted via scraping
- **No interlinking** between charger models

---

## PART 2 Summary: Page Structure Comparison

| Feature | 3W Battery | Inverter | Chargers |
|---------|-----------|----------|----------|
| Hero banner | Yes (product-specific) | Yes (home-context) | Yes (same for all) |
| Variant selector | Yes (11 tabs) | No (both shown together) | No (separate pages) |
| Product image | Per-variant | Single | Per-model |
| Description | Per-variant (tailored) | Single | Identical for all |
| Safety section | 4 icons (identical text) | 4 icons (different set) | None |
| "Why Choose" section | Yes (dual-column) | No (paragraph instead) | None |
| Spec section | Image per variant | Image (both variants) | Image per model |
| FAQ section | Yes (3 questions) | Yes (4 questions) | None |
| CTA section | None visible | None visible | None visible |
| Page depth | Very deep (11x repeat) | Medium | Very shallow |
| Interaction | Tab switching (no reload) | Static | Static |

---

## Architectural Insights for iTarang

### What Trontek Does Well
1. **Single-page multi-variant** approach for batteries avoids page bloat
2. **Tab-based variant switching** is good UX for comparing variants
3. **Safety features section** directly addresses the #1 buyer concern
4. **FAQ with pricing** captures long-tail SEO queries
5. **Product-specific hero banners** establish context immediately

### What Trontek Does Poorly
1. **All specs are image-locked** — not searchable, not accessible, not responsive
2. **Charger pages are extremely thin** — no differentiation, no FAQ, no safety info
3. **Identical copy across variants** — safety and "Why Choose" sections are copy-pasted
4. **No charger listing/index page** — poor discoverability
5. **No comparison tools** — users can't compare variants side by side
6. **No CTA on product pages** — no "Enquire Now" embedded in product sections
7. **No breadcrumbs** on product pages
8. **No related products** section
9. **Homepage carousel links to different URL** (`/3-wheeler` vs `/products/e-rickshaw-lithium-battery/`)

### Key Opportunities for iTarang
1. Build **HTML spec tables** (searchable, accessible, responsive)
2. Create a **unified charger page** with variant switching (like batteries)
3. Add **per-variant differentiated copy** instead of copy-paste
4. Include **CTA and lead capture** directly on product pages
5. Build **breadcrumbs and related products** for navigation
6. Add a **comparison mode** across variants
7. Include **video content and multiple product angles**

---

*Analysis complete. This document focuses on navigation and page flow only. See `trontek-product-specifications-deep-extract.md` for full specification data.*
