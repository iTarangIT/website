import Link from "next/link";
import { ArrowLeft, Clock, Calendar } from "lucide-react";
import Badge from "@/components/ui/Badge";
import ShareBar from "@/components/blog/ShareBar";

interface BlogLayoutProps {
  title: string;
  slug: string;
  date: string;
  readTime: string;
  category: string;
  children: React.ReactNode;
}

export default function BlogLayout({
  title,
  slug,
  date,
  readTime,
  category,
  children,
}: BlogLayoutProps) {
  return (
    <article className="py-16 md:py-24">
      <div className="mx-auto max-w-3xl px-4 sm:px-6">
        {/* Back link */}
        <Link
          href="/blog"
          className="inline-flex items-center gap-1.5 text-sm text-brand-600 hover:text-brand-700 mb-8 transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Blog
        </Link>

        {/* Article header */}
        <header className="mb-10">
          <Badge variant="default" className="mb-4">
            {category}
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

        {/* Article body */}
        <div className="prose prose-lg prose-gray max-w-none prose-headings:tracking-tight prose-a:text-brand-600 prose-a:no-underline hover:prose-a:underline prose-img:rounded-xl">
          {children}
        </div>

        {/* Article footer — back link + share */}
        <div className="mt-12 border-t border-gray-200 pt-8 flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
          <Link
            href="/blog"
            className="inline-flex items-center gap-1.5 text-sm text-brand-600 hover:text-brand-700 transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Blog
          </Link>
          <ShareBar title={title} slug={slug} />
        </div>
      </div>
    </article>
  );
}
