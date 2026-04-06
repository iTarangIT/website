import Link from "next/link";
import { Clock, Calendar } from "lucide-react";
import { Card } from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import type { BlogPost } from "@/data/blog-posts";

interface BlogCardProps {
  post: BlogPost;
}

export default function BlogCard({ post }: BlogCardProps) {
  const categoryColor =
    post.category === "Industry Insights"
      ? "from-brand-600 to-brand-800"
      : post.category === "Vision"
        ? "from-accent-sky to-brand-600"
        : "from-brand-700 to-accent-green";

  return (
    <Link href={`/blog/${post.slug}`} className="group block">
      <Card className="overflow-hidden transition-shadow hover:shadow-md h-full flex flex-col">
        {/* Cover placeholder */}
        <div className={`relative h-44 bg-gradient-to-br ${categoryColor} flex items-end p-5`}>
          <Badge variant="accent" className="absolute top-4 left-4 text-xs">
            {post.category}
          </Badge>
        </div>

        <div className="flex flex-col flex-1 p-5">
          <h3 className="text-lg font-bold text-gray-900 group-hover:text-brand-600 transition-colors line-clamp-2 mb-2">
            {post.title}
          </h3>
          <p className="text-sm text-gray-600 line-clamp-3 mb-4 flex-1">
            {post.excerpt}
          </p>
          <div className="flex items-center gap-4 text-xs text-gray-400">
            <span className="inline-flex items-center gap-1">
              <Calendar className="h-3.5 w-3.5" />
              {new Date(post.date).toLocaleDateString("en-IN", {
                day: "numeric",
                month: "short",
                year: "numeric",
              })}
            </span>
            <span className="inline-flex items-center gap-1">
              <Clock className="h-3.5 w-3.5" />
              {post.readTime}
            </span>
          </div>
        </div>
      </Card>
    </Link>
  );
}
