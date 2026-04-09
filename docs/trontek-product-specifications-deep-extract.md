# Trontek Product Specifications — Deep Extraction

> Detailed specification extraction for iTarang competitive reference.
> Scraped and analyzed on 2026-04-08 using Firecrawl + external source verification.
> **Scope:** 3W lithium batteries, inverter batteries, and EV chargers ONLY.
> **No copyrighted content copied verbatim. All specs structured from public sources.**

---

## Critical Note on Data Reliability

**Trontek's product specifications are presented as IMAGES (.jpg), not HTML text.**
This means Firecrawl cannot extract the actual numerical data from spec tables on trontek.com.

The spec data in this document comes from:
- **Trontek page text** (variant names, kWh, descriptions, FAQ) — RELIABLE
- **Amazon.in product listings** (dimensions, weight, warranty) — RELIABLE
- **IndiaMART listings** (model numbers, dimensions, capacity) — RELIABLE
- **Industry press articles** (Powercube specs from Energetica, ESS News) — RELIABLE
- **Trontek blog content** (range, cycle life, BMS features) — RELIABLE
- **Firecrawl AI extraction** (structured JSON from scrapeWithPrompt) — UNRELIABLE for numerical specs

Any spec marked with `[image-locked]` means it is visible only in the spec image on trontek.com and could not be verified from text sources. These values should NOT be trusted without manual verification.

---

## 1. E-Rickshaw / 3-Wheeler Lithium Batteries

### 1.1 Product Overview

- **Category:** E-Rickshaw Lithium Battery
- **Page URL:** `https://trontek.com/products/e-rickshaw-lithium-battery/`
- **Chemistry:** Lithium Iron Phosphate (LiFePO4)
- **Voltage levels:** 51V, 61V, 64V, 72V
- **Total variants:** 11
- **Model naming pattern:** TK-LiFe-[voltage x 10][capacity] (e.g., TK-LiFe-5145 for 51V 45AH)
- **Target customer:** E-rickshaw drivers, fleet operators
- **Use case:** Daily commercial e-rickshaw operations, urban last-mile transport

### 1.2 Variant Listing with Energy Values

| # | Variant | Voltage | Capacity | Energy (kWh) | Product Image |
|---|---------|---------|----------|-------------|---------------|
| 1 | 51V 105AH | 51V | 105 AH | 5.376 kWh | 51V 105AH main.png |
| 2 | 51V 132AH | 51V | 132 AH | 6.758 kWh | 51V 132AH.png |
| 3 | 51V 153AH | 51V | 153 AH | 7.834 kWh | 51V 132AH.png (reused) |
| 4 | 51V 232AH | 51V | 232 AH | 11.878 kWh | 51V 232AH.png |
| 5 | 61V 105AH | 61V | 105 AH | 6.405 kWh | 61V 105Ah d.png |
| 6 | 61V 132AH | 61V | 132 AH | 8.052 kWh | 61V 132AH.png |
| 7 | 61V 153AH | 61V | 153 AH | 9.333 kWh | 61V 153AH.png |
| 8 | 61V 232AH | 61V | 232 AH | 14.152 kWh | 61V 153AH.png (reused) |
| 9 | 64V 105AH | 64V | 105 AH | 6.72 kWh | 64V 105AH.png |
| 10 | 64V 132AH | 64V | 132 AH | 8.448 kWh | 64V 132AH.png |
| 11 | 72V 232AH | 72V | 232 AH | 16.704 kWh | 74V 232AH.png |

### 1.3 Verified Specifications — 51V 132AH (Reference Variant)

**Source: Amazon.in listing (B0G1N7BXP8)**

| Group | Spec | Value | Source |
|-------|------|-------|--------|
| **Electrical** | Nominal voltage | 51V | Trontek page |
| | Rated capacity | 132 AH | Trontek page |
| | Energy | 6.758 kWh | Trontek page |
| | Cell chemistry | LiFePO4 (Lithium Iron Phosphate) | Trontek page + blog |
| | Charging voltage | [image-locked] | — |
| | Charging current | [image-locked] | — |
| | Discharge current (continuous) | [image-locked] | — |
| | Peak discharge current | [image-locked] | — |
| | Cutoff voltage | [image-locked] | — |
| | Internal resistance | [image-locked] | — |
| **Mechanical** | Dimensions | 59 x 38 x 28.5 cm (D x W x H) | Amazon.in |
| | Weight | 54.1 kg | Amazon.in |
| | Casing/material | [image-locked] | — |
| | IP rating | [image-locked] | — |
| | Mounting type | Vehicle-mounted (e-rickshaw) | Contextual |
| **Operating Conditions** | Operating temp (discharge) | -20°C to 60°C | IndiaMART (TK-LiFe-5145 model) |
| | Operating temp (charging) | [image-locked] | — |
| | Storage temperature | [image-locked] | — |
| | Humidity | [image-locked] | — |
| **Performance** | Cycle life | 2000+ cycles at 25°C | IndiaMART listing + blog |
| | Range per charge | 80–120 km (varies with load/road) | Blog guide |
| | Battery lifespan | 3–6 years (varies with usage) | Trontek FAQ |
| | Charging time | [image-locked] | — |
| **Safety/BMS** | Overcharge protection | Yes | Trontek page |
| | Over-discharge protection | Yes | Trontek page |
| | Short circuit protection | Yes (no fire/explosion) | Trontek page |
| | Acupuncture/nail test | Passes without thermal runaway | Trontek page |
| | Thermal shock resistance | Withstands sudden temp changes | Trontek page |
| | Cell balancing | Yes (via BMS) | Blog |
| | BMS monitors | Voltage, current, SOC, SOH, temperature | Blog |
| **Certifications** | AIS certification | Referenced (Indian EV compliance) | Previous analysis |
| | Other certifications | [image-locked] | — |
| **Warranty/Service** | Warranty | 36 months | Amazon.in + FAQ |
| | Service | Via Trontek dealer network | FAQ |
| | Price reference | Starts from INR 55,000 | FAQ + IndiaMART |

### 1.4 Verified Specifications — TK-LiFe-5145 (51V 45AH, 2-Wheeler Model for Reference)

**Source: IndiaMART listing**

| Spec | Value |
|------|-------|
| Model | TK-LiFe-5145 |
| Voltage | 51V |
| Capacity | 45 AH |
| Energy | 2.3 kWh |
| Weight | ~20 kg |
| Dimensions | 47 x 33.4 x 28.3 cm |
| Cycle life | 2000+ at 25°C |
| Operating temp | -20°C to 60°C |
| Rated current | 16A |
| Max current | 24A |
| Warranty | 36 months |
| Features | Handle, breather, buzzer, secure connectors |

*Note: This is a 2-wheeler battery (45AH), not the 105AH e-rickshaw model. Listed for reference on available detailed specs.*

### 1.5 Common Features Across All E-Rickshaw Variants

From Trontek product page (text-based, verified):

**Safety Features (identical across all):**
- Overcharge/over-discharge protection via smart protection systems
- Short circuit resistance (no fire/explosion)
- Acupuncture test passed (no thermal runaway)
- Thermal shock resistance

**"Why Choose" Benefits (identical across all):**
- Attractive cycle life
- Extended safety performance
- Wide operating temperature range
- Unrivalled high temperature performance
- Green energy without metal contaminant
- High capacity
- Steady output voltage
- Little self-discharge
- Double safety protection
- High vibration and shock resistance

### 1.6 Per-Variant Description Summaries

| Variant | Key Positioning (from description) |
|---------|-----------------------------------|
| 51V 105AH | Standard daily commercial use, longer driving range, faster charging |
| 51V 132AH | High-performance, extended range, superior durability, commercial usage |
| 51V 153AH | Enhanced power, longer range for demanding routes, continuous commercial use |
| 51V 232AH | Maximum range, heavy-duty performance, fewer charging cycles |
| 61V 105AH | Optimized performance, daily commuting and commercial ops |
| 61V 132AH | Extended performance, longer driving range, high efficiency |
| 61V 153AH | Higher capacity, better efficiency, long-distance usage |
| 61V 232AH | Premium high-capacity, maximum range, heavy-duty, intensive daily ops |
| 64V 105AH | Efficient power delivery, city operations, reduced costs |
| 64V 132AH | Enhanced efficiency, longer range, energy savings |
| 72V 232AH | Highest capacity, maximum performance, long-distance and heavy-load |

### 1.7 Spec Image URLs (for manual verification)

These .jpg images on trontek.com contain the full spec tables. Manual inspection needed:

```
https://trontek.com/wp-content/themes/trontek/assets/img/51v-105ah-product.jpg
https://trontek.com/wp-content/themes/trontek/assets/img/51v-132ah-product.jpg
https://trontek.com/wp-content/themes/trontek/assets/img/51v-232ah-product.jpg
https://trontek.com/wp-content/themes/trontek/assets/img/61V-105Ah-product.jpg
https://trontek.com/wp-content/themes/trontek/assets/img/61V-132Ah-product.jpg
https://trontek.com/wp-content/themes/trontek/assets/img/61v-153ah-product.jpg
https://trontek.com/wp-content/themes/trontek/assets/img/61v-232ah-product.jpg
https://trontek.com/wp-content/themes/trontek/assets/img/64v-105ah-product.jpg
https://trontek.com/wp-content/themes/trontek/assets/img/64v-132ah-product.jpg
https://trontek.com/wp-content/themes/trontek/assets/img/73v-232ah-product.jpg
```

---

## 2. Inverter Batteries (Powercube)

### 2.1 Product Overview

- **Category:** Lithium Ion Battery for Inverter
- **Page URL:** `https://trontek.com/products/lithium-inverter-battery-home/`
- **Chemistry:** Lithium Iron Phosphate (LiFePO4)
- **Brand series:** Powercube
- **Variants:** 4 total (2 capacities x 2 tiers)
- **Target customer:** Homeowners, small businesses, solar users
- **Use case:** Home power backup, hybrid solar integration

### 2.2 Variant Structure

| Variant | Model | Voltage | Capacity | Energy | Tier | Display |
|---------|-------|---------|----------|--------|------|---------|
| Powercube 1.4 | (Standard) | 12.8V | 105 AH | 1.4 kWh | Standard | SOC indicator |
| Powercube 1.4+ | TK12100 | 12.8V | 105 AH | 1.4 kWh | Premium | LED status display |
| Powercube 2.7 | (Standard) | 25.6V | 105 AH | 2.7 kWh | Standard | No SOC display |
| Powercube 2.7+ | TK25100 | 25.6V | 105 AH | 2.7 kWh | Premium | LED status display |

*Note: The product page shows only "Powercube 1.4+" and "Powercube 2.7+" (Premium "+") variants. Standard variants exist but are not prominently featured on the page.*

### 2.3 Verified Specifications

**Sources: Energetica India, ESS News, Trontek page text**

| Group | Spec | Value | Source | Confidence |
|-------|------|-------|--------|------------|
| **Electrical** | Chemistry | LiFePO4 | Energetica India | HIGH |
| | Powercube 1.4 kWh voltage | 12.8V | ESS News + Energetica | HIGH |
| | Powercube 1.4 kWh capacity | 105 AH | ESS News + Energetica | HIGH |
| | Powercube 2.7 kWh voltage | 25.6V | ESS News + Energetica | HIGH |
| | Powercube 2.7 kWh capacity | 105 AH | ESS News + Energetica | HIGH |
| | Charging compatibility | Solar and grid | Energetica India | HIGH |
| | Charging voltage | [image-locked] | — | — |
| | Charging current | [image-locked] | — | — |
| | Discharge current | [image-locked] | — | — |
| | Internal resistance | [image-locked] | — | — |
| **Mechanical** | Design | Compact, sealed, lightweight | Energetica India | HIGH |
| | Dimensions (exact) | [image-locked] | — | — |
| | Weight (exact) | [image-locked] | — | — |
| | Maintenance | Zero maintenance | Energetica India | HIGH |
| **Performance** | Lifecycle | 4000+ charge cycles | ESS News + Energetica | HIGH |
| | Round-trip efficiency | >90% | ESS News + Energetica | HIGH |
| | Battery lifespan | 8–10 years | Trontek FAQ | HIGH |
| | Backup time | [image-locked] | — | — |
| **Safety/BMS** | Overcharge protection | Yes | Energetica India | HIGH |
| | Under-charge protection | Yes | Energetica India | HIGH |
| | Over-current protection | Yes | Energetica India | HIGH |
| | Under-current protection | Yes | Energetica India | HIGH |
| | Short-circuit protection | Yes | Energetica India | HIGH |
| | Thermal shutdown | Yes | Energetica India | HIGH |
| | Smart Control System | Monitors charging status, battery health, performance | Trontek page | HIGH |
| | BMS monitoring | Real-time SOC, SOH, voltage, temperature | Energetica India | HIGH |
| **Certifications** | Certifications | [image-locked] | — | — |
| **Solar** | Solar integration | Fully compatible with rooftop PV and hybrid inverters | Energetica India | HIGH |
| **Warranty** | Warranty | [not explicitly stated on page] | — | — |
| **Pricing** | Starting price | From Rs. 20,000 | Trontek FAQ | HIGH |

### 2.4 Feature Comparison: Powercube vs Page Icons

The inverter page uses DIFFERENT safety/feature icons than the battery page:

| Icon | Feature | Description |
|------|---------|-------------|
| Smart Control System | Monitors charging status, battery health and performance |
| High Safety | Prevents overcharging, overheating and short circuits |
| Long Life Battery | Thousands of charge cycles, longer lifespan |
| Advanced BMS Protection | Monitors voltage, temperature and charging levels |

### 2.5 Spec Image URL (for manual verification)

```
https://trontek.com/wp-content/themes/trontek/assets/img/Home%20(TK12100%20TK25100).jpg
```

This single image contains specs for BOTH TK12100 and TK25100 side by side.

---

## 3. EV Chargers (TK W-Series)

### 3.1 Product Overview

- **Category:** EV Chargers
- **Series:** W-Series
- **Models:** 5 (TK-500, TK-840, TK-1350, TK-2000, TK-3000)
- **Target use:** E-rickshaws, e-scooters, e-bikes, electric vehicles
- **Page structure:** Individual page per model, no combined listing

### 3.2 Model Listing

| Model | URL | Wattage (inferred) | Product Image | Spec Image |
|-------|-----|---------------------|---------------|------------|
| TK-500 W-Series | `/products/tk500-w-series` | 500W | TK500W.png | Tk-500.jpg |
| TK-840 W-Series | `/products/tk840-w-series` | 840W | TK840W.png | Tk-840.jpg |
| TK-1350 W-Series | `/products/tk1350-w-series` | 1350W | TK1350W.png | Tk-1350.jpg |
| TK-2000 W-Series | `/products/tk2000-w-series` | 2000W | TK2000W.png | Tk-2000.jpg |
| TK-3000 W-Series | `/products/tk3000-w-series` | 3000W | TK3000W.png | Tk-3000.jpg |

### 3.3 Verified Specifications — TK-500 W-Series

**Source: Amazon.in listing (B0G1HSQ3B9)**

| Group | Spec | Value | Source | Confidence |
|-------|------|-------|--------|------------|
| **General** | Model | TK-500 W-Series | Trontek page | HIGH |
| | Manufacturer | Trontek Electronics Ltd. | Amazon.in | HIGH |
| **Mechanical** | Dimensions | 12.2 x 18.7 x 6.8 cm (D x W x H) | Amazon.in | HIGH |
| | Weight | 1.65 kg | Amazon.in | HIGH |
| **Electrical** | Wattage | 500W (from model name) | Inferred | MEDIUM |
| | Input voltage | [image-locked] | — | — |
| | Output voltage | [image-locked] | — | — |
| | Output current | [image-locked] | — | — |
| | Efficiency | [image-locked] | — | — |
| **Protection** | Over-voltage protection | Yes | Amazon.in | HIGH |
| | Over-current protection | Yes | Amazon.in | HIGH |
| | Short-circuit protection | Yes | Amazon.in | HIGH |
| | Over-temperature protection | Yes | Amazon.in | HIGH |
| | Surge protection | Yes | Amazon.in | HIGH |
| **Features** | LED indicators | Charging status, power connection, full charge, fault alerts | Amazon.in | HIGH |
| | Compatibility | E-scooters, e-bikes, 2-wheelers, lithium battery systems | Amazon.in | HIGH |
| | Design | Compact, lightweight, plug-and-play | Amazon.in | HIGH |
| | Noise | Ultra-low noise | Amazon.in | HIGH |
| | Heat dissipation | Strong heat dissipation | Amazon.in | HIGH |
| **Warranty** | Warranty | 1 year | Amazon.in | HIGH |

### 3.4 Common Description (All 5 Models)

All charger pages share this identical description:
> "Our extensive product line of chargers covers multiple applications across various verticals. It comes with a hermetic and durable seal structure to provide a hassle-free charging experience. All our units are pre-tested for their efficiency, stability, reliability and protection."

### 3.5 Spec Image URLs (for manual verification)

```
https://trontek.com/wp-content/themes/trontek/assets/img/Tk-500.jpg
https://trontek.com/wp-content/themes/trontek/assets/img/Tk-840.jpg
https://trontek.com/wp-content/themes/trontek/assets/img/Tk-1350.jpg
https://trontek.com/wp-content/themes/trontek/assets/img/Tk-2000.jpg
https://trontek.com/wp-content/themes/trontek/assets/img/Tk-3000.jpg
```

### 3.6 Cross-Reference: Made-in-China TK-500 Data

A Made-in-China listing for a similar "TK-500" charger shows:
- Output: 12V/12A or 24V/6A
- Output power: 150W
- Battery type: Lead-acid / LiFePO4

**Confidence: LOW** — this may be a different product or older model. Do not rely on.

---

## 4. FAQ Data Extraction

### 4.1 E-Rickshaw Battery FAQ

| Question | Answer Summary |
|----------|---------------|
| Price of e-rickshaw lithium battery in India? | Starts from INR 55,000 depending on specs. Visit nearest Trontek dealer. |
| Why is lithium better for e-rickshaw? | Longer lifespan, lightweight, fast charging, improved range |
| How long does e-rickshaw lithium battery last? | 3 to 6 years depending on usage and charging |

### 4.2 Inverter Battery FAQ

| Question | Answer Summary |
|----------|---------------|
| What is a lithium ion battery for inverter? | Rechargeable battery for inverter systems, efficient backup during outages |
| Inverter battery price in India? | Starts from Rs. 20,000 depending on specs |
| Best inverter battery for home? | Lithium — longer life, faster charging, higher efficiency |
| How long does a lithium inverter battery last? | 8 to 10 years depending on usage |

### 4.3 Charger FAQ

No FAQ section exists on any charger page.

---

## 5. Presentation & Marketing Data

### 5.1 CTA Patterns

| Product | CTA Style | CTA Destination |
|---------|-----------|-----------------|
| All pages | "Enquire Now" in header | Form or WhatsApp (inferred) |
| E-rickshaw FAQ | "Visit nearest Trontek dealer" | Dealer network |
| Inverter FAQ | "Visit nearest Trontek dealer" | Dealer network |
| Blog | Links to product page | `/products/e-rickshaw-lithium-battery/` |
| Blog | Links to charger | `/products/tk500-w-series/` |

### 5.2 Trust Signals on Product Pages

- Safety features icon grid (batteries/inverters)
- "Trusted manufacturer" language in description
- BMS technology references
- AIS certification mentions
- Company established 2004
- 1 GWh production capacity
- 100,000+ e-rickshaws powered

### 5.3 SEO & Content Strategy

- Keyword-optimized page titles
- FAQ schema targeting long-tail queries
- Blog content funneling to product pages
- Open Graph tags properly configured
- No Product schema/structured data for rich results

---

## 6. What Could NOT Be Extracted

The following data is visible ONLY in spec sheet images on trontek.com and could not be extracted via any automated method:

### For E-Rickshaw Batteries (per variant):
- Exact charging voltage and current
- Discharge current (continuous and peak)
- Cutoff voltage
- Internal resistance
- Exact dimensions for all variants (only 51V 132AH from Amazon)
- Exact weight for all variants (only 51V 132AH from Amazon)
- Charging time
- Storage temperature range
- Humidity rating
- Altitude rating
- IP rating
- Casing material details
- Full certification list (AIS, BIS, ISO, IEC, UN38.3, RoHS, CE)

### For Inverter Batteries:
- Exact dimensions and weight per variant
- Charging/discharge voltage and current specs
- Internal resistance
- Backup time per variant
- Full certification list
- Warranty duration (not stated on product page)

### For Chargers:
- Input voltage and current
- Output voltage range and current
- Efficiency rating
- Power factor
- Connector type and charging protocol
- Operating temperature range
- Communication interface
- Exact specs for TK-840, TK-1350, TK-2000, TK-3000 (only TK-500 has Amazon data)

### Recommendation for Manual Extraction:
Download the spec images listed in sections 1.7, 2.5, and 3.5, then manually transcribe the data. These images are the definitive source for all detailed electrical and mechanical specifications.

---

*This document is a companion to `trontek-navigation-and-product-flow-analysis.md`. Together they provide the full competitive reference for iTarang product page development.*
