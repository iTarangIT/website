import Link from "next/link";
import { createMetadata } from "@/lib/metadata";
import { blogCategories, blogPosts } from "@/data/blog-posts";
import SectionHeading from "@/components/shared/SectionHeading";
import FadeInOnScroll from "@/components/shared/FadeInOnScroll";
import BlogCard from "@/components/blog/BlogCard";
import Badge from "@/components/ui/Badge";

export const metadata = createMetadata({
  title: "Blog & Insights",
  description:
    "Industry insights, product updates, and thought leadership on EV battery financing, lifecycle management, and India's electric mobility ecosystem.",
  path: "/blog",
});

export default function BlogPage() {
  return (
    <>
      <section className="relative overflow-hidden bg-brand-900 py-20 md:py-28">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-brand-700/30 via-transparent to-transparent" />
        <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 text-center">
          <Badge variant="accent" className="mb-6">Knowledge Hub</Badge>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-white tracking-tight mb-6">
            Blog &amp; Insights
          </h1>
          <p className="mx-auto max-w-2xl text-lg text-brand-200">
            Practical guidance and industry insight for India&apos;s electric mobility ecosystem.
          </p>
        </div>
      </section>

      <section aria-labelledby="topic-heading" className="border-b border-gray-100 bg-brand-50 py-12">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <SectionHeading badge="Explore by topic" title="Find the guidance you need" />
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {blogCategories.map((category) => (
              <Link
                key={category.slug}
                href={`/blog/category/${category.slug}`}
                className="rounded-xl border border-brand-100 bg-white p-5 transition-colors hover:border-brand-400"
              >
                <h2 className="font-semibold text-gray-900">{category.name}</h2>
                <p className="mt-2 text-sm text-gray-600">{category.description}</p>
              </Link>
            ))}
          </div>
        </div>
      </section>

      <section className="bg-white py-16 md:py-24">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <SectionHeading badge="Latest Articles" title="From the iTarang Team" />
          <div className="grid gap-8 sm:grid-cols-2">
            {blogPosts.map((post, i) => (
              <FadeInOnScroll key={post.slug} delay={i * 0.1}>
                <BlogCard post={post} />
              </FadeInOnScroll>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}
