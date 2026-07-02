# Image Placeholders — What's Needed & Where

Every spot on the site that currently shows a placeholder instead of a real image,
grouped by page. Drop the files into `public/images/` (suggested paths below), then
wire them up in the referenced component.

**Total needed: 27 images + 1–2 videos**

---

## 1. Home page (`/`)

### "Who We Serve" cards — 3 photos
Card header images, rendered at ~520×208px (landscape, roughly 5:2 crop).
File: `src/components/home/WhoWeServe.tsx` (lines 12, 22, 32)

| # | Placeholder text | Image needed | Suggested file |
|---|---|---|---|
| 1 | PHOTO: E-rickshaw driver | An e-rickshaw driver with their vehicle (candid, on the road or at a stand) | `public/images/audience/driver.webp` |
| 2 | PHOTO: Dealer shop | A battery dealer shop front / counter with stock visible | `public/images/audience/dealer-shop.webp` |
| 3 | PHOTO: Office / Dashboard | Lender-side shot — office setting or someone viewing the iTarang dashboard | `public/images/audience/lender-dashboard.webp` |

### Testimonial avatars — 3 headshots
Currently all three use the generic `/images/placeholder-avatar.svg`. Square headshots, ~200×200px min.
File: `src/components/home/SocialProof.tsx` (lines 18, 25, 32)

| # | Person | Image needed | Suggested file |
|---|---|---|---|
| 4 | Rajesh Kumar (driver) | Headshot of the driver giving the testimonial | `public/images/testimonials/rajesh-kumar.webp` |
| 5 | Sunil Sharma (dealer) | Headshot of the dealer | `public/images/testimonials/sunil-sharma.webp` |
| 6 | Priya Mehta (lender) | Headshot of the lender/NBFC contact | `public/images/testimonials/priya-mehta.webp` |

---

## 2. About page (`/about`)

File: `src/app/(marketing)/about/page.tsx`

### Founder section
| # | Placeholder | Image needed | Suggested file |
|---|---|---|---|
| 7 | "PHOTO: Founder headshot" (line 57) | Founder portrait — **square** crop (rendered aspect-square, ~400×400px min) | `public/images/team/founder.webp` |
| 8 | "60-second founder intro" video box (line 78) | Short founder intro **video** (16:9) + a poster/thumbnail image | video hosted or `public/videos/founder-intro.mp4` + `public/images/team/founder-video-poster.webp` |

### "From the Field" photo grid — 6 photos (4:3 landscape, lines 131–137)
| # | Placeholder label | Image needed | Suggested file |
|---|---|---|---|
| 9 | Team at work | Team candid — office or field work session | `public/images/field/team-at-work.webp` |
| 10 | Dealer visit | Team member visiting/onboarding a dealer | `public/images/field/dealer-visit.webp` |
| 11 | Battery warehouse | Warehouse racks with batteries in stock | `public/images/field/battery-warehouse.webp` |
| 12 | E-rickshaw with battery | E-rickshaw with an iTarang battery installed/visible | `public/images/field/erickshaw-battery.webp` |
| 13 | IoT device installation | Technician fitting the IoT tracker to a battery/vehicle | `public/images/field/iot-installation.webp` |
| 14 | Driver interaction | Team member talking with a driver | `public/images/field/driver-interaction.webp` |

> Note: `src/components/about/FounderVideoPlaceholder.tsx` ("Hear directly from our founders — Coming soon")
> and `src/components/about/FounderCard.tsx` are additional founder video/photo placeholders,
> currently not imported by any page. Same founder assets cover them if they get used.

---

## 3. How It Works page (`/how-it-works`)

### Lifecycle Journey — 6 images (one per stage)
File: `src/components/how-it-works/LifecycleJourney.tsx` (lines 32–87)

| # | Stage | Image needed | Suggested file |
|---|---|---|---|
| 15 | 01 Finance | PHOTO: Driver signing finance docs at a dealer counter | `public/images/lifecycle/01-finance.webp` |
| 16 | 02 Deploy | PHOTO: Battery being installed in an e-rickshaw | `public/images/lifecycle/02-deploy.webp` |
| 17 | 03 Monitor | **SCREENSHOT: IoT dashboard** (live battery health / portfolio view) | `public/images/lifecycle/03-monitor.webp` |
| 18 | 04 Maintain | PHOTO: Technician servicing a battery | `public/images/lifecycle/04-maintain.webp` |
| 19 | 05 Buyback | PHOTO: Collected/returned batteries at the warehouse | `public/images/lifecycle/05-buyback.webp` |
| 20 | 06 Recycle | PHOTO: Recycling facility / mineral extraction (partner facility ok) | `public/images/lifecycle/06-recycle.webp` |

### Battery spec cards — product photos
File: `src/components/how-it-works/BatterySpecs.tsx` (line 31) — the top-3 battery cards show
an icon + name instead of a product shot. The existing battery renders in
`public/images/` (e.g. `51V 105AH.png`) can be reused here — no new asset strictly required.

---

## 4. Partners page (`/partners`)

One image per partner tab, rendered 4:3.
File: `src/components/partners/PartnerTabs.tsx` (lines 61, 99, 137, 175)

| # | Tab | Image needed | Suggested file |
|---|---|---|---|
| 21 | NBFCs / Lenders | **SCREENSHOT: NBFC dashboard — portfolio health view** | `public/images/partners/nbfc-dashboard.webp` |
| 22 | Dealers | PHOTO: Dealer at their shop with iTarang batteries | `public/images/partners/dealer.webp` |
| 23 | OEMs | PHOTO: Battery manufacturing / quality check line | `public/images/partners/oem-manufacturing.webp` |
| 24 | Drivers / Customers | PHOTO: E-rickshaw driver with an iTarang battery | `public/images/partners/driver.webp` |

> The driver and dealer shots can double up with the Home "Who We Serve" photos if you
> shoot a couple of variants in one session.

---

## 5. Blog (`/blog`)

`src/data/blog-posts.ts` already points at cover images that **don't exist yet**
(`public/images/blog/` is missing), and `BlogCard.tsx` currently renders a gradient
instead. Covers should be ~16:9 landscape.

| # | Post | Image needed | Required file path (already referenced in code) |
|---|---|---|---|
| 25 | "Why 90% of E-Rickshaw Battery Financing Is Informal" | Cover: informal lending / cash-and-notebook vibe, or driver + money theme | `public/images/blog/informal-financing-cover.webp` |
| 26 | "The Battery Passport" | Cover: battery + data/QR/traceability theme | `public/images/blog/battery-passport-cover.webp` |

---

## 6. Investors page (`/investors`)

File: `src/components/investors/TeamSection.tsx` + `src/data/team.ts`

| # | Spot | Image needed | Suggested file |
|---|---|---|---|
| 27 | Founder cards (2) | Founder headshots — cards currently show initials in a colored circle. `team.ts` has an unused `image?` field waiting for paths (and placeholder names to replace) | `public/images/team/founder-ceo.webp`, `public/images/team/founder-cto.webp` |
| — | Advisor rows (3) | Optional — currently initial-letter avatars; real headshots only if advisors agree to be named | `public/images/team/advisor-*.webp` |

---

## 7. Products page (`/products`) — mostly covered, optional upgrades

- **Batteries**: all 11 SKU renders exist (`public/images/51V 105AH.png` … `72V 232AH.png`). ✅
- **Inverter (optional)**: all three models (1kW / 2kW / 3kW) share the single generic
  `invertor.jpeg`. Per-model photos would let `InverterProductView.tsx` show the right unit.
- **Charger (optional)**: same situation — one `charger.png` for all three models
  (48V 15A / 60V 20A / 72V 25A) in `ChargerProductView.tsx`.
- `ProductCard.tsx` (battery grid cards) shows a gradient + icon instead of the battery
  render — existing SKU images can be wired in, no new asset needed.

---

## Shoot checklist (to capture everything in one field day)

1. Founder: headshot (square) + 60-sec intro video
2. Driver: with e-rickshaw (wide), with battery (close), signing docs at dealer, talking with team
3. Dealer: shop front, at counter with iTarang batteries, team visiting
4. Warehouse: battery stock racks, collected/buyback batteries
5. Technician: installing battery in e-rickshaw, fitting IoT device, servicing a battery
6. Screenshots: IoT monitoring dashboard, NBFC portfolio-health dashboard view
7. Partner facilities (can be sourced from partners): manufacturing/QC line, recycling facility
8. Testimonial givers: 3 headshots (or reshoot with real customers)
9. Blog covers: 2 designed/edited images (16:9)
