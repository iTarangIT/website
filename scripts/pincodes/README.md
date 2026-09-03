# Pin-code areas for the nearest-dealer search

`src/data/pincode-areas.ts` maps a three-digit Indian pin-code prefix to a point
and a district name. It is what turns a visitor typing "226001" into somewhere on
the map when the curated gazetteer has nothing for that prefix.

## Source

**GeoNames postal codes, India** — <https://download.geonames.org/export/zip/IN.zip>
(1.7 MB, rebuilt daily; the copy this table was generated from was stamped
2026-09-03). Licence, quoted from `https://download.geonames.org/export/zip/readme.txt`:

> This work is licensed under a Creative Commons Attribution 4.0 License.

Attribution: "Postal code data © GeoNames, CC BY 4.0, https://www.geonames.org".
The same licence family as the Survey of India outline in `scripts/geo/README.md`,
so this adds no new obligation beyond the credit line, which is repeated in the
header of the generated file.

GeoNames was chosen over the data.gov.in *All India Pincode Directory* — which is
GODL-India and would also be usable — because data.gov.in returns HTTP 403 to a
plain automated fetch and needs a registered `api.data.gov.in` key. A key is a
secret, and secrets do not belong in a build step (CLAUDE.md §4).

## What the generator does with it

Measured on the file itself, not assumed: 155,570 rows, 19,238 distinct pin codes,
about 8 post offices per pin code, no row missing coordinates.

1. **Median per pin code, then median per prefix.** Offices sharing a pin code do
   *not* share a coordinate — pin 744301 alone carries three points, and the worst
   pin spans 703 km. The median is used at both levels because it ignores those
   outliers; a mean would not.
2. **The state is whichever polygon actually contains the point**, tested against
   `src/data/india-map-paths.ts`. This is self-correcting where GeoNames is stale:
   it still files Ladakh under Jammu & Kashmir, and the containment test puts the
   194x prefixes back in Ladakh without a hand-written exception.
3. **The district name** is the most common `admin_name2` in the prefix.

## Why three digits and not six

Six-digit precision costs about 400 KB and buys nothing here. Checked against the
78 hand-curated towns in `src/lib/dealers/gazetteer.ts`, prefix centres land a
median **11 km** from the curated coordinate (p90 32 km, worst 65 km) — district
level, which is all that is needed to rank dealers that sit hundreds of km apart.

Precision where dealers actually trade does not come from this table anyway:
`src/lib/dealers/locate.ts` consults the curated gazetteer's own `pins` first and
only falls through to here for the long tail.

## Rebuild

```bash
bash scripts/pincodes/fetch.sh     # downloads into .work/ (gitignored)
npm run pincodes:build             # regenerates src/data/pincode-areas.ts
```

The generator fails loudly rather than emitting a doubtful row: it reports how
many prefixes fell outside every polygon and how many disagreed with
`stateFromPincode`, and throws if the totals move far from what is recorded here.
