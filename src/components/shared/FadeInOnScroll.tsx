"use client";

import { type ReactNode } from "react";
import { motion } from "framer-motion";
import { useInView } from "react-intersection-observer";
import { cn } from "@/lib/utils";

interface FadeInOnScrollProps {
  children: ReactNode;
  direction?: "up" | "left" | "right" | "none";
  delay?: number;
  className?: string;
}

const directionOffsets = {
  up: { x: 0, y: 40 },
  left: { x: -40, y: 0 },
  right: { x: 40, y: 0 },
  none: { x: 0, y: 0 },
};

export default function FadeInOnScroll({
  children,
  direction = "up",
  delay = 0,
  className,
}: FadeInOnScrollProps) {
  const { ref, inView } = useInView({
    triggerOnce: true,
    threshold: 0.15,
  });

  const offset = directionOffsets[direction];

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, x: offset.x, y: offset.y }}
      animate={
        inView
          ? { opacity: 1, x: 0, y: 0 }
          : { opacity: 0, x: offset.x, y: offset.y }
      }
      transition={{ duration: 0.6, ease: "easeOut", delay }}
      className={cn(className)}
    >
      {children}
    </motion.div>
  );
}
