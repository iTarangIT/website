This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.

## NBFC Demo Dashboard

A static, sales-only demo dashboard lives at `/nbfc/dashboard` and showcases what an NBFC partner experience on iTarang looks like.

**How to show it:**

1. From any page, click **NBFC Login** in the header.
2. On `/login`, click **Login as Demo NBFC** (no password — one-click demo).
3. You land on the dashboard at `/nbfc/dashboard`.

**What to walk the prospect through:**

- **Overview** — Portfolio KPIs (batteries financed, active loans, AUM, NPA vs. industry, lead-to-disbursement time, default recovery rate) and today's AI dialer activity donut.
- **Leads** — 8 demo driver applications in a card grid with iTarang scores, status, and a prominent **Call with AI Dialer** button.
- **AI Dialer modal (the hero moment)** — Click the call button on any lead to open a simulated live call. The Hindi/English transcript reveals line-by-line, and the right-hand extraction panel auto-populates fields (identity, earnings, route, sentiment) as the conversation progresses, ending with a qualification score.

All data is static mock data in `src/lib/nbfc-mock-data.ts`. Auth is a demo `localStorage` flag — the code contains a `// TODO: replace with real auth before production` marker on the login handler. The marketing site is untouched apart from the single **NBFC Login** CTA added to the global header.
