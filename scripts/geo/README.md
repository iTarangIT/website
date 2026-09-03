# India state boundaries for the dealer map

`india-states.topo.json` is the committed source for `src/data/india-map-paths.ts`
(rebuilt with `npm run map:build`). It is a simplified TopoJSON of the 28 states
and 8 union territories, one feature each, property `name`.

## Why this outline

An Indian company's site has to draw the external boundary the way the
Government of India publishes it: full Jammu & Kashmir and Ladakh extent,
Arunachal Pradesh included. GADM, Natural Earth and geoBoundaries files do not,
so they are not acceptable here regardless of licence.

## Sources

1. **Outline (all external and inter-state lines):** Survey of India state
   boundaries, downloaded from <https://indiamaps.gov.in/soiapp/> and mirrored
   by the DataMeet community at
   `datameet/maps` → `Survey-of-India-Index-Maps/StateBoundary/` (shapefile,
   Web Mercator). Licence: CC BY 4.0 — attribution "Survey of India state
   boundaries via DataMeet India community (CC BY 4.0)". Fetched 2026-09-03.

   That download predates two reorganisations, which the build script fixes:
   - Daman & Diu and Dadra & Nagar Haveli appear as separate rows; they were
     merged into one union territory in January 2020, so they are dissolved
     into "Dadra and Nagar Haveli and Daman and Diu".
   - Ladakh (a separate UT since October 2019) is not split from Jammu &
     Kashmir.

2. **Ladakh / J&K internal line only:** the `Ladakh` polygon from
   `udit-001/india-maps-data` (commit `2884453`, `topojson/india.json`, no
   licence stated, "curated from publicly available sources"). It is used as a
   cutter: J&K = SoI polygon minus Ladakh cutter (largest piece), Ladakh = SoI
   polygon minus that J&K body. The outer outline therefore remains Survey of
   India's in every direction; only the ~600 km line between the two UTs comes
   from the second source. Resulting areas — J&K 53,378 km², Ladakh
   169,690 km² — match the Government of India figures for the two UTs.

## Rebuild

```bash
bash scripts/geo/build-topo.sh          # downloads into scripts/geo/.work, writes india-states.topo.json
npm run map:build                       # regenerates src/data/india-map-paths.ts and re-checks cities
```

The script is the authoritative record of the exact mapshaper commands
(reprojection, dissolve, the Ladakh cut, `-simplify interval=2500 keep-shapes`,
`-filter-islands min-area=2km2`). Open the result in <https://mapshaper.org>
after any change to confirm the J&K/Ladakh extent, Telangana, and 36 features.
