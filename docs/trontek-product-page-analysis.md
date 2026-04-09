# Trontek Product Page Analysis

> Competitive research for iTarang product page design and development.
> Scraped and analyzed on 2026-04-08 using Firecrawl.
> **This document contains analysis and structured notes only — no copyrighted content has been copied verbatim.**

---

## Source URLs Analyzed

| # | URL | Page Type |
|---|-----|-----------|
| 1 | `https://trontek.com/` | Homepage |
| 2 | `https://trontek.com/products/e-rickshaw-lithium-battery/` | E-Rickshaw Lithium Battery (product detail) |
| 3 | `https://trontek.com/products/lithium-inverter-battery-home/` | Inverter Battery for Home (product detail) |
| 4 | `https://trontek.com/products/electric-scooter-battery/` | Electric Scooter Battery (product detail) |
| 5 | Full sitemap (100+ URLs via Firecrawl `map`) | Site architecture |

---

## Executive Summary

Trontek (est. 2004) is one of India's largest lithium battery manufacturers. Their website is a WordPress-based, SEO-heavy product catalog targeting both B2B (dealers, fleet operators) and B2C (e-rickshaw drivers, homeowners) audiences. The site follows a **product-category-first** architecture where each major product line gets a dedicated long-form page containing all variants. Their design is functional rather than cutting-edge — heavy on trust signals, specifications, and safety messaging. The approach is very effective for the Indian market where buyers are price-sensitive and safety-conscious.

**Key takeaway for iTarang:** Trontek's strength is information density and trust-building. Their weakness is visual storytelling and modern UX. iTarang has an opportunity to match their information depth while delivering a significantly better user experience.

---

## Site Architecture Overview

### Navigation Structure
- **Products** (main nav) links to individual product category pages
- Product categories: E-Rickshaw Battery, Electric Scooter Battery, Inverter Battery, Golf Cart, Drones/Solid State, EV Chargers, MHE, Industrial BESS, Solar
- **About**, **Management**, **Blog**, **News & Events**, **Contact**
- No centralized "all products" grid page (the `/products` page returned minimal content)

### Product Organization Pattern
- Each product category = one long single-page with all variants stacked vertically
- Variants are selectable via a tab/button strip at the top (e.g., "51V 105AH", "51V 132AH", etc.)
- No individual per-variant URLs — everything lives on the parent category page
- This is a single-page multi-product approach (vs. separate pages per SKU)

### URL Structure
```
/products/e-rickshaw-lithium-battery/
/products/lithium-inverter-battery-home/
/products/electric-scooter-battery/
/products/golf-cart/
/products/solid-state/
```

---

## Product Page Structure Breakdown

### Consistent Section Order (Every Product Page)

Each product detail page follows this exact structure, repeated for every variant:

```
1. Hero Banner Image (full-width, product photography)
2. Variant Selector (horizontal tab strip)
3. Product Title + Variant Name + kWh Capacity
4. Product Image (centered, isolated product shot)
5. Product Description (1 paragraph, benefit-focused)
6. Safety Features Section (icon grid, 4 items)
7. "Why Choose Trontek" Section (dual-column bullet list)
8. Product Specifications (image of spec table)
9. FAQ Section (accordion, 3-4 questions)
```

### Section-by-Section Analysis

#### 1. Hero Banner
- Full-width banner image at the very top
- Product-specific imagery (e-rickshaw on road, inverter in home setting)
- **Pattern:** Lifestyle/contextual image showing the product in use
- **Why it works:** Immediately establishes use-case context for the visitor

#### 2. Variant Selector
- Horizontal strip of clickable options (e.g., "51V 105AH", "51V 132AH", "51V 153AH", etc.)
- Located just below the hero banner
- **Pattern:** Tab-based variant switching without page reload
- **Why it works:** Buyers can compare variants quickly without navigating away
- **For e-rickshaw page:** 11 variants across 4 voltage levels (51V, 61V, 64V, 72V)
- **For scooter page:** 4 variants
- **For inverter page:** 2 variants (Powercube 1.4+ and 2.7+)

#### 3. Product Title + Capacity Badge
- Large heading: "E Rickshaw Lithium Battery"
- Sub-heading with variant and total energy: "51V 132AH (6.758kWh)"
- **Pattern:** Technical specification right in the title — speaks to informed buyers
- **Why it works:** Indian e-rickshaw buyers care about AH and kWh first

#### 4. Product Image
- Clean, isolated product photo on neutral/white background
- Single angle, professional photography
- **Pattern:** Standard e-commerce product photography
- **Weakness:** Only one angle, no 360-degree view or zoom

#### 5. Product Description
- Single paragraph, benefit-focused
- Mentions: performance, range, charging speed, durability, commercial usage
- Tailored per variant (higher-capacity variants emphasize range/heavy-duty)
- **Pattern:** Technical copywriting that addresses buyer concerns directly
- **Keyword-heavy** for SEO (e.g., "lithium battery for e rickshaw", "LiFePO4")

#### 6. Safety Features (Icon Grid)
- 4-icon grid layout
- Consistent across ALL products:
  - Over-charge / Over-discharge protection
  - Short circuit protection
  - Acupuncture/Thermal stability test
  - Thermal shock resistance
- Each has: icon, title, 1-2 sentence description
- **Pattern:** Safety certification-style icon grid
- **Why it works:** Indian EV market is plagued by battery fire concerns. Safety messaging is critical for conversion. This section directly addresses the #1 buyer fear.

#### 7. "Why Choose" Section
- Dual-column bullet list (10 total bullet points)
- Split into two columns of 5 items each
- Left column: cycle life, safety, temperature range, green energy
- Right column: capacity, voltage stability, self-discharge, protection, vibration resistance
- **Pattern:** Feature checklist with technical benefits
- **Weakness:** Very repetitive across all products — identical text for every variant

#### 8. Product Specifications
- **Presented as an IMAGE (not an HTML table)**
- Spec sheet image showing: voltage, capacity, energy, dimensions, weight, cycle life, charging specs, operating temperature, certifications
- **Pattern:** Image-based spec table (probably exported from a PDF/catalog)
- **Why this is notable:** Using images instead of HTML tables means specs aren't searchable, not accessible, and can't be easily updated. This is a weakness we can exploit.
- Different spec image per variant

#### 9. FAQ Section
- 3-4 questions per product page
- Accordion-style expand/collapse
- Questions cover: price range, why lithium is better, battery lifespan, warranty
- **Pattern:** SEO-optimized FAQ schema
- **Why it works:** Captures long-tail search queries ("what is the price of e rickshaw lithium battery in India")

---

## UI/UX Patterns

### Visual Design
- **Color scheme:** Dark navy/blue with white text for headers, clean white sections for content
- **Typography:** Standard sans-serif, nothing distinctive
- **Image quality:** Professional product photography, but limited angles
- **Layout:** Single-column content flow, full-width sections alternating between dark and light backgrounds
- **WordPress theme:** Custom theme with standard WordPress/WP patterns

### Navigation UX
- Desktop mega-menu with product categories
- Sticky header (implied from standard WP setup)
- "Enquire Now" CTA button visible in header
- No product search functionality observed
- No filtering or comparison tool

### Content Strategy
- **SEO-first approach:** Every page title and description is keyword-optimized
- Heavy use of structured data / Open Graph tags
- Blog content supports product pages (guides like "Complete Guide to E-Rickshaw Lithium Batteries in India")
- **Content depth:** Each product page is very long (e-rickshaw page was 30,000+ characters)

### Responsiveness
- `viewport` meta tag set for mobile
- Layout appears to be responsive (standard WordPress responsive theme)
- No specific mobile-first patterns observed from the markup

---

## Product Categorization & Variant Strategy

### How Trontek Organizes Products

```
Products (top-level)
  |-- E-Rickshaw Lithium Battery
  |     |-- 51V 105AH, 132AH, 153AH, 232AH
  |     |-- 61V 105AH, 132AH, 153AH, 232AH
  |     |-- 64V 105AH, 132AH
  |     |-- 72V 232AH
  |
  |-- Electric Scooter Battery
  |     |-- 51V 45AH, 51V 60AH
  |     |-- 61V 48AH
  |     |-- 64V 32AH
  |
  |-- Lithium Inverter Battery (Home)
  |     |-- Powercube 1.4+ (1.4 kWh)
  |     |-- Powercube 2.7+ (2.7 kWh)
  |
  |-- Golf Cart Battery
  |-- Solid State / LMNC / Snap Fit
  |-- MHE Batteries
  |-- Industrial BESS
  |-- Solar Street Light
  |-- EV Chargers (TK500, TK840, TK1350, TK2000, TK3000 W-Series)
  |-- Hybrid Inverters (Single Phase, Three Phase Light/Heavy)
  |-- Solar GTI
```

### Naming Convention
- Voltage + Capacity format: "51V 132AH"
- kWh displayed in parentheses: "(6.758kWh)"
- Product line names: "Powercube" for inverter series
- Series names for chargers: "TK500 W-Series"

### Insight for iTarang
- Trontek's taxonomy is voltage-first, which works for technical buyers
- For iTarang, consider a use-case-first taxonomy (e.g., "For Daily Commuters" vs. "For Fleet Operators") that then maps to voltage/capacity variants
- The tab-based variant switching is a good UX pattern worth adapting

---

## Technical Specification Presentation

### What Trontek Shows
- Voltage, Capacity (AH), Energy (kWh)
- Dimensions (L x W x H)
- Weight
- Cycle life
- Charging voltage and current
- Operating temperature range
- BMS features
- Certifications (AIS-certified for EV products)

### How They Show It
- **Image-based spec sheets** (not interactive HTML)
- One spec image per variant
- Professional but static — cannot be searched, copied, or compared

### What's Missing
- No side-by-side comparison tool
- No interactive spec table
- No "which battery is right for me?" recommendation flow
- No downloadable PDF datasheets (at least not linked from product pages)

### Opportunity for iTarang
- Build **interactive HTML spec tables** (searchable, accessible, responsive)
- Add a **comparison mode** where users can compare 2-3 variants side by side
- Create a **"battery selector" tool** — answer 3-4 questions, get a recommendation
- Offer downloadable PDF spec sheets as lead magnets

---

## Safety & Trust-Building Patterns

### Trust Signals Used by Trontek

| Signal Type | How They Use It |
|-------------|-----------------|
| Safety icon grid | 4 safety features on every product page (overcharge, short circuit, thermal, acupuncture) |
| "Trusted manufacturer" language | "One of the trusted manufacturers of e rickshaw lithium batteries in India" |
| BMS messaging | Multiple mentions of Battery Management System |
| Certification references | AIS certification mentioned (relevant for Indian EV compliance) |
| Founder visibility | CEO photo and name on homepage ("Samrath Jit Singh") |
| Media coverage | Entire "News & Events" section showing press features (ET, YourStory, EV Mechanica, etc.) |
| Production capacity claims | "1 GWh production capacity" |
| Install base claims | "100,000+ e-rickshaws powered" |
| Company history | "Established in 2004" — longevity as trust signal |
| FAQ with pricing transparency | Gives starting prices in FAQ ("starts from 55,000 INR") |
| Warranty information | "3-year warranty" mentioned in FAQs |

### What Works
- The **safety features section** directly addresses the biggest buyer concern (battery fires)
- **Press/media logos** create instant credibility
- **Founder face + name** humanizes the brand
- **Production capacity** signals scale and reliability

### What's Missing
- No customer testimonials or reviews
- No video content (no factory tours, no product demos)
- No certification badges/logos displayed visually
- No third-party quality seals (ISO, BIS logos)
- No case studies from fleet operators

---

## CTA & Conversion Patterns

### CTAs Observed
- **"Enquire Now"** — primary header CTA (likely opens a form or WhatsApp)
- **"View More"** — on homepage product cards (links to product detail pages)
- **No "Buy Now" or "Add to Cart"** — this is not an e-commerce site
- **No pricing on product pages** — directs to dealers ("visit nearest Trontek dealer")
- **FAQ mentions starting prices** — e.g., "starts from 55,000 INR" and "starts from Rs. 20,000"

### Conversion Flow
```
Homepage/Search → Product Category Page → Read Specs → Enquire Now → Dealer/Sales
```

### What's Effective
- Dealer-based model means no cart complexity
- "Enquire Now" as persistent CTA removes decision paralysis
- Pricing anchoring in FAQ ("starts from X") gives buyers a reference without full price commitment

### What's Missing
- No EMI calculator (critical for Indian market)
- No dealer locator / nearest store finder
- No WhatsApp click-to-chat on product pages
- No "request callback" option
- No lead capture form directly on product pages

### Opportunity for iTarang
- iTarang already has an EMI calculator component — this is a major differentiator
- Add WhatsApp deep links on every product page
- Build a dealer locator or service center finder
- Implement a "request quote" form with pre-selected product variant

---

## Content & SEO Strategy

### What Trontek Does Well
- **Keyword-rich page titles:** "E Rickshaw Lithium Battery | Price & Specifications in India"
- **Dedicated blog content** supporting each product line with educational guides
- **FAQ schema** targeting long-tail queries
- **Open Graph / social meta** properly configured
- **Internal linking** from blog posts to product pages

### Blog Strategy
- Educational content: "Complete Guide to E-Rickshaw Lithium Batteries in India"
- Comparison content: "Lead Acid vs Lithium-Ion"
- Pricing content: "E-Rickshaw Battery Price in India"
- These articles funnel organic traffic to product pages

### SEO Weaknesses
- Spec tables as images (not indexable)
- No structured data for products (no Product schema/rich results)
- Repetitive content across variants (same safety/features text)

---

## What We Should Adapt for iTarang

### High-Priority (Implement These)
1. **Variant tab selector** — Let users switch between battery variants without page reload
2. **Safety features icon grid** — Address battery safety concerns prominently (adapt for iTarang's specific safety tech)
3. **Spec tables** — But as interactive HTML, not images
4. **FAQ section** — With proper schema markup for SEO
5. **kWh-in-title pattern** — Show capacity prominently, Indian buyers care about this
6. **Dual-column feature list** — Effective for scanning key benefits
7. **Blog-to-product funnel** — Educational content that links to product pages

### Medium-Priority (Improve On These)
8. **Product photography** — Multiple angles, 360-degree view, lifestyle shots
9. **Hero banner with contextual imagery** — Show batteries in real vehicles/homes
10. **Press/media trust strip** — If iTarang has press coverage, showcase it
11. **Founder visibility** — Already present in iTarang's about page, cross-link to product pages

### iTarang-Specific Advantages to Leverage
12. **EMI Calculator** — Already built, deploy on every product page
13. **WhatsApp integration** — Already built, embed on product pages
14. **Modern React/Next.js stack** — Can build interactive comparison tools, animations, better UX
15. **Data-driven approach** — Battery health monitoring / fleet dashboard as unique selling point

---

## What We Should NOT Copy

1. **Image-based spec tables** — Use real HTML tables instead (accessible, searchable, responsive)
2. **Identical copy across all variants** — The "Why Choose" and "Safety Features" text is 100% identical for every variant on every product. Write differentiated copy per variant.
3. **No customer testimonials** — Add real testimonials, especially from fleet operators
4. **No video content** — Add product demo videos, factory tour, installation guides
5. **Dealer-only pricing model** — Consider showing indicative pricing if possible
6. **WordPress approach** — iTarang's Next.js stack is already superior for performance and UX
7. **Repetitive section structure** — While consistency is good, the exact same 5 sections per variant feels like a template. Make each variant feel considered.
8. **Missing comparison tools** — Don't replicate this gap; build a comparison feature
9. **No mobile-first design language** — Build mobile-first from the start

---

## Recommended Ideas for iTarang Product Pages

### E-Rickshaw / 3-Wheeler Batteries

**Page structure recommendation:**
```
1. Hero: Full-width lifestyle image (e-rickshaw on Indian road)
2. Problem statement: "Why your lead-acid battery is costing you more"
3. Product selector: Interactive variant picker (voltage x capacity matrix)
4. Selected variant detail:
   a. Product image (multiple angles)
   b. Key stats strip (range, charging time, weight, warranty)
   c. Interactive spec table
   d. Safety features (with iTarang-specific BMS features)
5. Comparison: Lead-acid vs Lithium toggle (already built as ComparisonToggle component)
6. EMI Calculator (already built)
7. Fleet operator testimonials
8. "Which battery is right for you?" recommendation quiz
9. FAQ (with schema)
10. CTA: WhatsApp enquiry + Request quote form
```

**Differentiation from Trontek:**
- Show real-world range data ("120 km per charge in Delhi traffic")
- Highlight iTarang's data/monitoring platform as a unique feature
- Add installation video or guide
- Include TCO (Total Cost of Ownership) calculator

### Inverter Batteries

**Page structure recommendation:**
```
1. Hero: Home power backup scenario (Indian home during power cut)
2. "Power your home differently" value proposition
3. Product variants (Powercube equivalent)
4. Feature grid with smart home integration angle
5. Spec comparison table (HTML, responsive)
6. Solar compatibility section
7. EMI Calculator
8. Customer reviews
9. FAQ
10. CTA: Buy / Enquire via WhatsApp
```

**Differentiation from Trontek:**
- Emphasize smart monitoring (app-connected battery status)
- Show solar integration pathway
- Include power backup duration calculator ("How long can you run X appliances?")

### General Product Page UX Improvements Over Trontek

| Area | Trontek | iTarang Opportunity |
|------|---------|---------------------|
| Spec display | Static images | Interactive, filterable HTML tables |
| Comparison | None | Side-by-side variant comparison tool |
| Pricing | "Visit dealer" only | Indicative pricing + EMI calculator |
| Social proof | Press logos only | Customer testimonials + fleet case studies |
| Media | Single product photo | Multi-angle photos + video |
| Mobile UX | Basic responsive | Mobile-first design, swipe gestures |
| Lead capture | Generic "Enquire Now" | Contextual CTAs with pre-filled product info |
| Content | Repetitive per variant | Unique, benefit-driven copy per variant |
| Accessibility | Image-based specs | WCAG-compliant HTML content |
| Performance | WordPress (heavy) | Next.js (fast, SSR/SSG) |

---

## Existing iTarang Components to Reuse

Based on the current codebase, these components are already built and should be deployed on product pages:

| Component | Location | Use On Product Page |
|-----------|----------|---------------------|
| `ComparisonToggle` | `src/components/products/ComparisonToggle.tsx` | Lead-acid vs Lithium comparison |
| `EMICalculator` | `src/components/products/EMICalculator.tsx` | Financing section |
| `ProductCard` | `src/components/products/ProductCard.tsx` | Related products / variant cards |
| `SpecTable` | `src/components/products/SpecTable.tsx` | Technical specifications |
| `WhatsAppButton` | `src/components/shared/WhatsAppButton.tsx` | CTA integration |
| `CTASection` | `src/components/shared/CTASection.tsx` | Bottom-of-page conversion |
| `TrustBadgeStrip` | `src/components/shared/TrustBadgeStrip.tsx` | Trust signals |
| `FadeInOnScroll` | `src/components/shared/FadeInOnScroll.tsx` | Scroll animations |
| `SectionHeading` | `src/components/shared/SectionHeading.tsx` | Consistent section titles |

---

*This document is a working reference for the iTarang product page redesign. It should be used alongside the actual design process to inform section order, content strategy, and component development.*
