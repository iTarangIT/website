"use client";

import { cn } from "@/lib/utils";
import {
  forwardRef,
  type AnchorHTMLAttributes,
  type ButtonHTMLAttributes,
  type ForwardedRef,
} from "react";

type Variant = "primary" | "secondary" | "outline" | "ghost" | "accent";
type Size = "sm" | "md" | "lg";

type SharedProps = {
  variant?: Variant;
  size?: Size;
};

type ButtonElementProps = SharedProps &
  Omit<ButtonHTMLAttributes<HTMLButtonElement>, keyof SharedProps> & {
    href?: undefined;
  };

type AnchorElementProps = SharedProps &
  Omit<AnchorHTMLAttributes<HTMLAnchorElement>, keyof SharedProps> & {
    href: string;
  };

export type ButtonProps = ButtonElementProps | AnchorElementProps;

const baseStyles =
  "inline-flex items-center justify-center font-semibold rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-brand-400 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed";

const variantClasses: Record<Variant, string> = {
  primary: "bg-brand-500 text-white hover:bg-brand-600 shadow-lg shadow-brand-500/25",
  secondary: "bg-brand-100 text-brand-700 hover:bg-brand-200",
  outline: "border-2 border-brand-500 text-brand-500 hover:bg-brand-50",
  ghost: "text-brand-600 hover:bg-brand-50",
  accent: "bg-accent-sky text-white hover:bg-accent-sky/90 shadow-lg shadow-accent-sky/25",
};

const sizeClasses: Record<Size, string> = {
  sm: "px-4 py-2 text-sm",
  md: "px-6 py-3 text-base",
  lg: "px-8 py-4 text-lg",
};

const Button = forwardRef<HTMLButtonElement | HTMLAnchorElement, ButtonProps>(
  (props, ref) => {
    if (props.href !== undefined) {
      const { variant = "primary", size = "md", className, children, ...rest } = props;
      return (
        <a
          {...rest}
          ref={ref as ForwardedRef<HTMLAnchorElement>}
          className={cn(baseStyles, variantClasses[variant], sizeClasses[size], className)}
        >
          {children}
        </a>
      );
    }

    const { variant = "primary", size = "md", className, children, ...rest } = props;
    return (
      <button
        {...rest}
        ref={ref as ForwardedRef<HTMLButtonElement>}
        className={cn(baseStyles, variantClasses[variant], sizeClasses[size], className)}
      >
        {children}
      </button>
    );
  },
);

Button.displayName = "Button";
export default Button;
