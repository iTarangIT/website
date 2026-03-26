import { cn } from "@/lib/utils";
import { forwardRef, type TextareaHTMLAttributes } from "react";

const Textarea = forwardRef<HTMLTextAreaElement, TextareaHTMLAttributes<HTMLTextAreaElement>>(
  ({ className, ...props }, ref) => (
    <textarea
      ref={ref}
      className={cn(
        "w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-sm text-gray-900 placeholder:text-gray-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 transition-colors min-h-[100px] resize-y",
        className
      )}
      {...props}
    />
  )
);
Textarea.displayName = "Textarea";
export default Textarea;
