import { ShieldCheck, Zap, Wifi, Settings } from "lucide-react";
import FadeInOnScroll from "@/components/shared/FadeInOnScroll";

const defaultIcons = [ShieldCheck, Zap, Wifi, Settings];

interface Feature {
  title: string;
  description: string;
}

interface GenericFeaturesProps {
  title: string;
  highlightWord: string;
  subtitle: string;
  features: Feature[];
}

export default function GenericFeatures({ title, highlightWord, subtitle, features }: GenericFeaturesProps) {
  return (
    <div className="p-8 md:p-12 bg-white">
      <div className="text-center mb-8">
        <h2 className="font-sans text-2xl md:text-[30px] font-extrabold uppercase tracking-wide text-[#0a2540] mb-3">
          {title} <span className="text-brand-600">{highlightWord}</span>
        </h2>
        <p className="text-sm text-[#64748b] leading-relaxed max-w-2xl mx-auto font-sans">
          {subtitle}
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
        {features.map((feature, i) => {
          const Icon = defaultIcons[i % defaultIcons.length];
          return (
            <FadeInOnScroll key={feature.title} delay={i * 0.05}>
              <div className="group rounded-xl border border-gray-200/60 bg-[#f8fafc] p-6 hover:shadow-lg hover:shadow-brand-500/5 hover:border-brand-200/50 transition-all h-full">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-500/10 mb-4 group-hover:bg-brand-500/15 transition-colors">
                  <Icon className="h-5 w-5 text-brand-500" />
                </div>
                <h3 className="text-[17px] font-bold text-gray-900 mb-2 font-sans group-hover:text-brand-600 transition-colors">
                  {feature.title}
                </h3>
                <p className="text-sm text-gray-600 leading-relaxed font-sans">
                  {feature.description}
                </p>
              </div>
            </FadeInOnScroll>
          );
        })}
      </div>
    </div>
  );
}
