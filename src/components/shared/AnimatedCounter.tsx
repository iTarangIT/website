"use client";

import CountUp from "react-countup";
import { useInView } from "react-intersection-observer";

interface AnimatedCounterProps {
  value: number;
  prefix?: string;
  suffix?: string;
  label: string;
  duration?: number;
}

export default function AnimatedCounter({
  value,
  prefix = "",
  suffix = "",
  label,
  duration = 2.5,
}: AnimatedCounterProps) {
  const { ref, inView } = useInView({
    triggerOnce: true,
    threshold: 0.3,
  });

  return (
    <div ref={ref} className="text-center">
      <div className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white">
        {inView ? (
          <CountUp
            start={0}
            end={value}
            duration={duration}
            prefix={prefix}
            suffix={suffix}
            separator=","
          />
        ) : (
          <span>
            {prefix}0{suffix}
          </span>
        )}
      </div>
      <p className="mt-2 text-sm sm:text-base text-white/80">{label}</p>
    </div>
  );
}
