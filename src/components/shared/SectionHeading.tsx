import { cn } from "@/lib/utils";

interface SectionHeadingProps {
  title: string;
  subtitle?: string;
  badge?: string;
  align?: "left" | "center";
  dark?: boolean;
  className?: string;
}

export default function SectionHeading({
  title,
  subtitle,
  badge,
  align = "center",
  dark = false,
  className,
}: SectionHeadingProps) {
  return (
    <div
      className={cn(
        "max-w-3xl mb-12 md:mb-16",
        align === "center" && "mx-auto text-center",
        align === "left" && "text-left",
        className
      )}
    >
      {badge && (
        <span
          className={cn(
            "inline-block mb-3 px-4 py-1.5 text-xs font-semibold uppercase tracking-widest rounded-full",
            dark
              ? "text-brand-200 bg-brand-800"
              : "text-brand-600 bg-brand-100"
          )}
        >
          {badge}
        </span>
      )}
      <h2
        className={cn(
          "text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight",
          dark ? "text-white" : "text-gray-900"
        )}
      >
        {title}
      </h2>
      {subtitle && (
        <p
          className={cn(
            "mt-4 text-lg md:text-xl leading-relaxed",
            dark ? "text-brand-200" : "text-gray-600",
            align === "center" && "mx-auto max-w-2xl"
          )}
        >
          {subtitle}
        </p>
      )}
    </div>
  );
}
