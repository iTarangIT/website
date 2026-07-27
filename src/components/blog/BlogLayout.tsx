import Link from "next/link";
import { ArrowLeft, Clock, Calendar } from "lucide-react";
import Badge from "@/components/ui/Badge";
import { blogCategories, type BlogCategorySlug } from "@/data/blog-posts";

interface BlogLayoutProps {
  title: string;
  date: string;
  readTime: string;
  category: BlogCategorySlug;
  children: React.ReactNode;
}

export default function BlogLayout({
  title,
  date,
  readTime,
  category,
  children,
}: BlogLayoutProps) {
  const categoryDetails = blogCategories.find(({ slug }) => slug === category);

  return (
    <article className="py-16 md:py-24">
      <div className="mx-auto max-w-3xl px-4 sm:px-6">
        <Link
          href="/blog"
          className="inline-flex items-center gap-1.5 text-sm text-brand-600 hover:text-brand-700 mb-8 transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Blog
        </Link>

        <nav aria-label="Breadcrumb" className="mb-6 text-sm text-gray-500">
          <Link href="/" className="hover:text-brand-600">Home</Link>
          <span className="mx-2">/</span>
          <Link href="/blog" className="hover:text-brand-600">Blog</Link>
          <span className="mx-2">/</span>
          <Link href={`/blog/category/${category}`} className="hover:text-brand-600">
            {categoryDetails?.name}
          </Link>
          <span className="mx-2">/</span>
          <span aria-current="page">Article</span>
        </nav>

        <header className="mb-10">
          <Badge variant="default" className="mb-4">
            {categoryDetails?.name}
          </Badge>
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-gray-900 tracking-tight mb-4">
            {title}
          </h1>
          <div className="flex items-center gap-4 text-sm text-gray-500">
            <span className="inline-flex items-center gap-1.5">
              <Calendar className="h-4 w-4" />
              {new Date(date).toLocaleDateString("en-IN", {
                day: "numeric",
                month: "long",
                year: "numeric",
              })}
            </span>
            <span className="inline-flex items-center gap-1.5">
              <Clock className="h-4 w-4" />
              {readTime}
            </span>
          </div>
        </header>

        <div className="prose prose-lg prose-gray max-w-none prose-headings:tracking-tight prose-a:text-brand-600 prose-a:no-underline hover:prose-a:underline prose-img:rounded-xl">
          {children}
        </div>

        <div className="mt-12 border-t border-gray-200 pt-8 flex items-center justify-between">
          <Link
            href={`/blog/category/${category}`}
            className="inline-flex items-center gap-1.5 text-sm text-brand-600 hover:text-brand-700 transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            More in {categoryDetails?.name}
          </Link>
          <p className="text-sm text-gray-400">Share this article</p>
        </div>
      </div>
    </article>
  );
}
