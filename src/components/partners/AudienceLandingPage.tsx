import type { ReactNode } from "react";
import Button from "@/components/ui/Button";

export type AudiencePage = {
  eyebrow: string;
  title: string;
  intro: string;
  /** Optional block rendered between the hero and the cards, e.g. the dealer map. */
  afterHero?: ReactNode;
  sections: { title: string; body: ReactNode }[];
  primaryCta: string;
  primaryHref: string;
  secondaryCta: string;
  secondaryHref: string;
};

export default function AudienceLandingPage({ page }: { page: AudiencePage }) {
  return (
    <>
      <section className="relative overflow-hidden bg-surface-warm px-4 pb-16 pt-28 md:pb-24 md:pt-36">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_left,rgba(5,27,154,0.08),transparent_60%)]" />
        <div className="relative z-10 mx-auto max-w-5xl">
          <span className="mb-4 inline-block font-sans text-sm font-semibold uppercase tracking-widest text-brand-500">
            {page.eyebrow}
          </span>
          <h1 className="max-w-4xl text-5xl leading-[1.05] tracking-tight text-gray-900 md:text-7xl">
            {page.title}
          </h1>
          <p className="mt-6 max-w-3xl font-sans text-xl leading-relaxed text-gray-600">
            {page.intro}
          </p>
          <div className="mt-8 flex flex-wrap gap-4">
            <Button href={page.primaryHref} size="lg">{page.primaryCta}</Button>
            <Button href={page.secondaryHref} variant="outline" size="lg">{page.secondaryCta}</Button>
          </div>
        </div>
      </section>

      {page.afterHero}

      <section className="bg-white px-4 py-16 md:py-24">
        <div className="mx-auto grid max-w-5xl gap-10 md:grid-cols-2">
          {page.sections.map((section) => (
            <article key={section.title} className="rounded-2xl border border-gray-200 bg-gray-50 p-7">
              <h2 className="text-2xl tracking-tight text-gray-900">{section.title}</h2>
              <div className="mt-4 font-sans leading-relaxed text-gray-600">{section.body}</div>
            </article>
          ))}
        </div>
      </section>

      <section className="bg-surface-warm px-4 py-16 text-center md:py-20">
        <div className="mx-auto max-w-3xl">
          <h2 className="text-3xl tracking-tight text-gray-900">Ready to discuss your requirements?</h2>
          <p className="mt-4 font-sans text-lg leading-relaxed text-gray-600">
            Share your context with the iTarang team. We will confirm the relevant product, financing, service, or lifecycle workflow before proposing next steps.
          </p>
          <div className="mt-7">
            <Button href={page.primaryHref} size="lg">{page.primaryCta}</Button>
          </div>
        </div>
      </section>
    </>
  );
}
