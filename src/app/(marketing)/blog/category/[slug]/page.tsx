import Link from "next/link";
import { notFound } from "next/navigation";
import { createMetadata } from "@/lib/metadata";
import { blogCategories, blogPosts, type BlogCategorySlug } from "@/data/blog-posts";
import BlogCard from "@/components/blog/BlogCard";

interface CategoryPageProps {
  params: Promise<{ slug: string }>;
}

export function generateStaticParams() {
  return blogCategories.map(({ slug }) => ({ slug }));
}

export async function generateMetadata({ params }: CategoryPageProps) {
  const { slug } = await params;
  const category = blogCategories.find(({ slug: categorySlug }) => categorySlug === slug);
  if (!category) return {};

  return {
    ...createMetadata({
      title: `${category.name} | Blog & Insights`,
      description: category.description,
      path: `/blog/category/${category.slug}`,
    }),
    robots: { index: false, follow: true },
  };
}

export default async function BlogCategoryPage({ params }: CategoryPageProps) {
  const { slug } = await params;
  const category = blogCategories.find(({ slug: categorySlug }) => categorySlug === slug);
  if (!category) {
    notFound();
  }

  const posts = blogPosts.filter(({ category: postCategory }) => postCategory === slug as BlogCategorySlug);

  return (
    <main className="py-16 md:py-24">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <nav aria-label="Breadcrumb" className="mb-8 text-sm text-gray-500">
          <Link href="/" className="hover:text-brand-600">Home</Link>
          <span className="mx-2">/</span>
          <Link href="/blog" className="hover:text-brand-600">Blog</Link>
          <span className="mx-2">/</span>
          <span aria-current="page">{category.name}</span>
        </nav>
        <header className="mb-12 max-w-3xl">
          <p className="mb-3 text-sm font-semibold uppercase tracking-wider text-brand-600">Topic archive</p>
          <h1 className="text-4xl font-bold tracking-tight text-gray-900">{category.name}</h1>
          <p className="mt-4 text-lg text-gray-600">{category.description}</p>
        </header>
        {posts.length > 0 ? (
          <div className="grid gap-8 sm:grid-cols-2">
            {posts.map((post) => <BlogCard key={post.slug} post={post} />)}
          </div>
        ) : (
          <p className="rounded-xl border border-dashed border-gray-300 p-8 text-gray-600">
            New articles for this topic will appear here as the editorial hub grows.
          </p>
        )}
      </div>
    </main>
  );
}
